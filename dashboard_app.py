import streamlit as st
import mysql.connector
import pandas as pd
import warnings
import altair as alt

# Suppress Pandas SQLAlchemy warning
warnings.filterwarnings("ignore", category=UserWarning)

# -------------------------------
# Database connection
# -------------------------------
def get_connection():
    return mysql.connector.connect(
        host=st.secrets["MYSQLHOST"],
        port=st.secrets["MYSQLPORT"],
        user=st.secrets["MYSQLUSER"],
        password=st.secrets["MYSQLPASSWORD"],
        database=st.secrets["MYSQLDATABASE"]
    )

def run_query(query, params=None):
    conn = get_connection()
    df = pd.read_sql(query, conn, params=params)
    conn.close()
    return df

# -------------------------------
# App Title
# -------------------------------
st.title("🎾 Tennis Analytics Dashboard")
st.caption("ℹ️ Data source: Doubles competitor rankings API — only doubles data available.")

# -------------------------------
# Sidebar Filters
# -------------------------------
st.sidebar.header("🔎 Filters")

name_search = st.sidebar.text_input("Search by competitor name")
country_filter = st.sidebar.text_input("Filter by country")
rank_range = st.sidebar.slider("Filter by rank range", 1, 100, (1, 10))
points_threshold = st.sidebar.number_input("Minimum points", min_value=0, value=0)
gender_filter = st.sidebar.selectbox("Gender", ["All", "Men", "Women"])

# -------------------------------
# Homepage Summary
# -------------------------------
st.header("📊 Summary Statistics")

total_competitors = run_query("SELECT COUNT(*) AS total FROM Competitors")
countries = run_query("SELECT COUNT(DISTINCT country) AS countries FROM Competitors")
highest_points = run_query("SELECT MAX(points) AS max_points FROM Competitor_Rankings")

col1, col2, col3 = st.columns(3)
col1.metric("Total Competitors", int(total_competitors['total'][0]))
col2.metric("Countries Represented", int(countries['countries'][0]))
col3.metric("Highest Points", int(highest_points['max_points'][0]))

# -------------------------------
# Competitors Table with Filters
# -------------------------------
st.header("👥 Competitors")

query = """
SELECT c.name, c.country, cr.ranking, cr.points, cr.movement, cr.competitions_played, cr.type, cr.gender
FROM Competitors c
JOIN Competitor_Rankings cr ON c.competitor_id = cr.competitor_id
WHERE cr.ranking BETWEEN %s AND %s
"""
params = [rank_range[0], rank_range[1]]

if name_search:
    query += " AND c.name LIKE %s"
    params.append(f"%{name_search}%")
if country_filter:
    query += " AND c.country = %s"
    params.append(country_filter)
if points_threshold > 0:
    query += " AND cr.points >= %s"
    params.append(points_threshold)
if gender_filter != "All":
    query += " AND cr.gender = %s"
    params.append(gender_filter)

results = run_query(query, params)
st.dataframe(results)

# -------------------------------
# Competitor Details Viewer
# -------------------------------
st.header("👤 Competitor Details Viewer")

if not results.empty:
    competitor_name = st.selectbox("Select competitor", results['name'].unique())
    if competitor_name:
        detail_query = """
        SELECT c.name, c.country, cr.ranking, cr.movement, cr.points, cr.competitions_played, cr.type, cr.gender
        FROM Competitors c
        JOIN Competitor_Rankings cr ON c.competitor_id = cr.competitor_id
        WHERE c.name = %s
        """
        detail = run_query(detail_query, [competitor_name])
        st.table(detail)

# -------------------------------
# Country-Wise Analysis
# -------------------------------
st.header("🌍 Country-Wise Analysis")

country_stats = run_query("""
SELECT c.country, COUNT(c.competitor_id) AS competitor_count, AVG(cr.points) AS avg_points
FROM Competitors c
JOIN Competitor_Rankings cr ON c.competitor_id = cr.competitor_id
GROUP BY c.country
ORDER BY competitor_count DESC
""")
st.dataframe(country_stats)

st.subheader("Competitors per Country (Bar Chart)")
chart = alt.Chart(country_stats).mark_bar().encode(
    x=alt.X("country", sort="-y"),
    y="competitor_count",
    tooltip=["country", "competitor_count", "avg_points"]
).properties(width=700)
st.altair_chart(chart)

# -------------------------------
# Leaderboards
# -------------------------------
st.header("🏆 Leaderboards")

top_ranked = run_query("""
SELECT c.name, c.country, cr.ranking, cr.points
FROM Competitors c
JOIN Competitor_Rankings cr ON c.competitor_id = cr.competitor_id
ORDER BY cr.ranking ASC
LIMIT 10
""")
st.subheader("Top Ranked Competitors")
st.table(top_ranked)

top_points = run_query("""
SELECT c.name, c.country, cr.ranking, cr.points
FROM Competitors c
JOIN Competitor_Rankings cr ON c.competitor_id = cr.competitor_id
ORDER BY cr.points DESC
LIMIT 10
""")
st.subheader("Competitors with Highest Points")
st.table(top_points)

# Ranking distribution histogram
st.subheader("Ranking Distribution")
ranking_data = run_query("SELECT ranking FROM Competitor_Rankings")
hist = alt.Chart(ranking_data).mark_bar().encode(
    x=alt.X("ranking", bin=alt.Bin(maxbins=50)),
    y="count()"
).properties(width=700)
st.altair_chart(hist)

# Points vs Ranking line chart
st.subheader("Points vs Ranking (Top 20)")
trend_data = run_query("""
SELECT c.name, cr.ranking, cr.points
FROM Competitors c
JOIN Competitor_Rankings cr ON c.competitor_id = cr.competitor_id
ORDER BY cr.ranking ASC
LIMIT 20
""")
line = alt.Chart(trend_data).mark_line(point=True).encode(
    x="ranking",
    y="points",
    tooltip=["name", "ranking", "points"]
).properties(width=700)
st.altair_chart(line)
