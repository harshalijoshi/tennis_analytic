import streamlit as st
from data_loader import collect_data
import pandas as pd
import mysql.connector

st.title("🎾 Tennis Data Loader")

# Utility: clear tables safely
def clear_tables(cursor, tables):
    cursor.execute("SET SQL_SAFE_UPDATES = 0")
    cursor.execute("SET FOREIGN_KEY_CHECKS = 0")
    for t in tables:
        cursor.execute(f"DELETE FROM {t}")
    cursor.execute("SET FOREIGN_KEY_CHECKS = 1")
    cursor.execute("SET SQL_SAFE_UPDATES = 1")

# -------------------------------
# 1) Competitions + Categories
# -------------------------------
df_comp = collect_data("competitions", "competitions.csv", "competitions")

if not df_comp.empty:
    categories = df_comp[["category.id", "category.name"]].drop_duplicates()
    categories = categories.rename(columns={"category.id": "category_id", "category.name": "category_name"})
    st.subheader("📂 Categories Table")
    st.dataframe(categories)

    competitions = df_comp[["id", "name", "parent_id", "type", "gender", "category.id"]].rename(
        columns={"id": "competition_id", "name": "competition_name", "category.id": "category_id"}
    )
    st.subheader("🏆 Competitions Table")
    st.dataframe(competitions)

    def insert_competitions(categories_df, competitions_df):
        try:
            conn = mysql.connector.connect(host="localhost", user="root", password="password@123", database="tennis_db")
            cursor = conn.cursor()

            clear_tables(cursor, ["Competitions", "Categories"])

            for _, row in categories_df.iterrows():
                cursor.execute(
                    "REPLACE INTO Categories (category_id, category_name) VALUES (%s, %s)",
                    (str(row["category_id"]), str(row["category_name"]))
                )
            for _, row in competitions_df.iterrows():
                parent_id = None if pd.isna(row["parent_id"]) else str(row["parent_id"])
                cursor.execute(
                    """REPLACE INTO Competitions 
                       (competition_id, competition_name, parent_id, type, gender, category_id) 
                       VALUES (%s, %s, %s, %s, %s, %s)""",
                    (str(row["competition_id"]), str(row["competition_name"]), parent_id,
                     str(row["type"]), str(row["gender"]), str(row["category_id"]))
                )
            conn.commit(); cursor.close(); conn.close()
            return f"✅ Competitions & Categories refreshed! ({len(categories_df)} categories, {len(competitions_df)} competitions)"
        except Exception as e:
            return f"❌ Error: {e}"

    if st.button("Insert Competitions into MySQL"):
        st.success(insert_competitions(categories, competitions))


# -------------------------------
# 2) Complexes + Venues
# -------------------------------
df_complex = collect_data("complexes", "complexes.csv", "complexes")

if not df_complex.empty:
    complexes = df_complex[["id", "name"]].drop_duplicates().rename(columns={"id": "complex_id", "name": "complex_name"})
    st.subheader("🏟️ Complexes Table")
    st.dataframe(complexes)

    venues_expanded = df_complex.explode("venues").reset_index(drop=True).dropna(subset=["venues"])
    venues_expanded["venue_id"] = venues_expanded["venues"].apply(lambda v: v.get("id"))
    venues_expanded["venue_name"] = venues_expanded["venues"].apply(lambda v: v.get("name"))
    venues_expanded["city_name"] = venues_expanded["venues"].apply(lambda v: v.get("city_name"))
    venues_expanded["country_name"] = venues_expanded["venues"].apply(lambda v: v.get("country_name"))
    venues_expanded["country_code"] = venues_expanded["venues"].apply(lambda v: v.get("country_code"))
    venues_expanded["timezone"] = venues_expanded["venues"].apply(lambda v: v.get("timezone"))
    venues_expanded["complex_id"] = venues_expanded["id"]

    venues = venues_expanded[["venue_id", "venue_name", "city_name", "country_name", "country_code", "timezone", "complex_id"]]
    st.subheader("🎾 Venues Table")
    st.dataframe(venues)

    def insert_complexes(complexes_df, venues_df):
        try:
            conn = mysql.connector.connect(host="localhost", user="root", password="password@123", database="tennis_db")
            cursor = conn.cursor()

            clear_tables(cursor, ["Venues", "Complexes"])

            for _, row in complexes_df.iterrows():
                cursor.execute(
                    "REPLACE INTO Complexes (complex_id, complex_name) VALUES (%s, %s)",
                    (str(row["complex_id"]), str(row["complex_name"]))
                )
            for _, row in venues_df.iterrows():
                cursor.execute(
                    """REPLACE INTO Venues 
                       (venue_id, venue_name, city_name, country_name, country_code, timezone, complex_id) 
                       VALUES (%s, %s, %s, %s, %s, %s, %s)""",
                    (str(row["venue_id"]), str(row["venue_name"]),
                     str(row["city_name"]) if row["city_name"] else "Unknown",
                     str(row["country_name"]) if row["country_name"] else "Unknown",
                     str(row["country_code"]) if row["country_code"] else "UNK",
                     str(row["timezone"]) if row["timezone"] else "Unknown",
                     str(row["complex_id"]))
                )
            conn.commit(); cursor.close(); conn.close()
            return f"✅ Complexes & Venues refreshed! ({len(complexes_df)} complexes, {len(venues_df)} venues)"
        except Exception as e:
            return f"❌ Error: {e}"

    if st.button("Insert Complexes into MySQL"):
        st.success(insert_complexes(complexes, venues))
    print("Venues count:", len(venues))
    print(venues.sort_values("venue_id").head(20))

# -------------------------------
# 3) Doubles Competitor Rankings
# -------------------------------
df_rankings = collect_data("double_competitors_rankings", "double_competitors_rankings.csv", "double_competitors_rankings")

if not df_rankings.empty:
    df_expanded = df_rankings.explode("competitor_rankings").reset_index(drop=True).dropna(subset=["competitor_rankings"])
    comp_details = pd.json_normalize(df_expanded["competitor_rankings"])
    df_final = pd.concat([df_expanded.drop(columns=["competitor_rankings"]), comp_details], axis=1)

    competitors = df_final[["competitor.id", "competitor.name", "competitor.country",
                            "competitor.country_code", "competitor.abbreviation"]].drop_duplicates().rename(
        columns={"competitor.id": "competitor_id", "competitor.name": "name",
                 "competitor.country": "country", "competitor.country_code": "country_code",
                 "competitor.abbreviation": "abbreviation"})
    st.subheader("👤 Competitors Table")
    st.dataframe(competitors)

    rankings = df_final[["rank", "movement", "points", "competitions_played", "competitor.id", "gender", "type_id"]].rename(
        columns={"competitor.id": "competitor_id", "rank": "ranking", "type_id": "type"})
    type_map = {"1": "singles", "2": "doubles", "3": "mixed"}
    rankings["type"] = rankings["type"].astype(str).map(type_map).fillna("unknown")
    st.subheader("📊 Competitor Rankings Table")
    st.dataframe(rankings)

    def insert_rankings(competitors_df, rankings_df):
        try:
            conn = mysql.connector.connect(host="localhost", user="root", password="password@123", database="tennis_db")
            cursor = conn.cursor()

            clear_tables(cursor, ["Competitor_Rankings", "Competitors"])

            for _, row in competitors_df.iterrows():
                cursor.execute(
                    """REPLACE INTO Competitors 
                       (competitor_id, name, country, country_code, abbreviation) 
                       VALUES (%s, %s, %s, %s, %s)""",
                    (str(row["competitor_id"]), str(row["name"]), str(row["country"]),
                     str(row["country_code"]), str(row["abbreviation"]))
                )
            for _, row in rankings_df.iterrows():
                cursor.execute(
                    """REPLACE INTO Competitor_Rankings 
                       (ranking, movement, points, competitions_played, competitor_id, type, gender) 
                       VALUES (%s, %s, %s, %s, %s, %s, %s)""",
                    (int(row["ranking"]), int(row["movement"]), int(row["points"]),
                     int(row["competitions_played"]), str(row["competitor_id"]),
                     str(row["type"]), str(row["gender"]))
                )
            conn.commit(); cursor.close(); conn.close()
            return f"✅ Competitors & Rankings refreshed! ({len(competitors_df)} competitors, {len(rankings_df)} rankings)"
        except Exception as e:
            return f"❌ Error: {e}"

    if st.button("Insert Doubles Rankings into MySQL"):
        st.success(insert_rankings(competitors, rankings))
