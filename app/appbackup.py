
import streamlit as st
import pandas as pd
import plotly.express as px
from sqlalchemy import create_engine, text
from sqlalchemy.engine import URL


# ============================================================
# 1. PAGE CONFIGURATION & VISUAL STYLE
# ============================================================
st.set_page_config(
    page_title="Solar Analytics and Energy Insights",
    page_icon="☀️",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.markdown(
    """
    <style>
      .block-container {padding-top: 1.7rem; padding-bottom: 2.5rem; max-width: 1500px;}
      [data-testid="stSidebar"] {border-right: 1px solid rgba(128,128,128,.18);}
      .hero {
        padding: 1.5rem 1.7rem; border-radius: 18px; margin-bottom: 1.2rem;
        background: linear-gradient(115deg, #102b3f 0%, #155e58 58%, #27815f 100%);
        color: #ffffff;
      }
      .hero h1 {font-size: 2.15rem; line-height: 1.2; margin: 0 0 .45rem 0; color: #ffffff;}
      .hero p {font-size: 1rem; margin: 0; color: #e6f4ef;}
      .eyebrow {font-size: .76rem; text-transform: uppercase; letter-spacing: .12em; font-weight: 700; color: #bde7d4; margin-bottom: .45rem;}
      .section-note {color: #64748b; font-size: .92rem; margin-top: -.35rem;}
      div[data-testid="stMetric"] {background: var(--secondary-background-color); padding: 1rem 1.1rem; border: 1px solid rgba(128,128,128,.18); border-radius: 14px;}
      div[data-testid="stMetricLabel"] p {font-size: .88rem;}
      div[data-testid="stMetricValue"] {font-size: 1.55rem;}
      .insight-card {padding: 1rem 1.1rem; border: 1px solid rgba(128,128,128,.2); border-radius: 14px; margin-bottom: .8rem;}
      .insight-card h3 {margin: 0 0 .45rem 0; font-size: 1.05rem;}
      .small-muted {font-size: .84rem; color: #64748b;}
      footer {visibility: hidden;}
    </style>
    """,
    unsafe_allow_html=True,
)


# ============================================================
# 2. DATABASE CONNECTION & SHARED HELPERS
# ============================================================
@st.cache_resource
def get_connection():
    config = st.secrets["mysql"]

    connection_url = URL.create(
        drivername="mysql+pymysql",
        username=config["username"],
        password=config["password"],
        host=config["host"],
        port=int(config["port"]),
        database=config["database"],
    )

    return create_engine(connection_url, pool_pre_ping=True)


def read_query(query, engine, params=None):
    return pd.read_sql(text(query), engine, params=params or {})


def get_date_limits(engine, table_name):
    result = read_query(
        f"""
        SELECT
            MIN(DATE(DATE_TIME)) AS min_date,
            MAX(DATE(DATE_TIME)) AS max_date
        FROM {table_name}
        """,
        engine,
    ).iloc[0]

    return (
        pd.to_datetime(result["min_date"]).date(),
        pd.to_datetime(result["max_date"]).date(),
    )


def date_filter(engine, table_name, label, key_prefix):
    min_date, max_date = get_date_limits(engine, table_name)

    left, right = st.columns(2)

    with left:
        start = st.date_input(
            f"{label} start date",
            value=min_date,
            min_value=min_date,
            max_value=max_date,
            key=f"{key_prefix}_start",
        )

    with right:
        end = st.date_input(
            f"{label} end date",
            value=max_date,
            min_value=min_date,
            max_value=max_date,
            key=f"{key_prefix}_end",
        )

    if start > end:
        st.error("The start date cannot be later than the end date.")
        return None

    return {
        "start_date": start,
        "end_date": end,
    }


def chart_layout(fig, y_title=None):
    fig.update_layout(
        template="plotly_white",
        hovermode="x unified",
        margin=dict(l=15, r=15, t=65, b=15),
        legend_title_text="",
        font=dict(family="Arial, sans-serif", size=12),
    )

    if y_title:
        fig.update_yaxes(title_text=y_title)

    fig.update_xaxes(showgrid=False)
    fig.update_yaxes(gridcolor="rgba(148,163,184,.22)")

    return fig


def page_heading(title, description):
    st.title(title)

    st.markdown(
        f'<p class="section-note">{description}</p>',
        unsafe_allow_html=True,
    )


# ============================================================
# 3. HEADER & NAVIGATION
# ============================================================
st.markdown(
    """
    <div class="hero">
      <div class="eyebrow">Data Analytics Capstone Project</div>
      <h1>☀️ Solar Analytics and Energy Insights</h1>
      <p>Explore solar generation, weather relationships, household electricity patterns and SQL-driven insights.</p>
    </div>
    """,
    unsafe_allow_html=True,
)

with st.sidebar:
    st.markdown("## ☀️ Analytics Hub")
    st.caption("Solar generation • Weather • Consumption")

    selected_page = st.radio(
        "Navigate",
        [
            "Overview",
            "Solar Generation",
            "Weather Analysis",
            "Household Consumption",
            "SQL Reports",
            "Business Insights",
            "Data Quality",
        ],
        label_visibility="collapsed",
    )

    st.divider()
    st.caption("**Project tools**")
    st.caption("Python · Pandas · MySQL · SQL · Plotly · Streamlit")


# ============================================================
# 4. CONNECT TO MYSQL
# ============================================================
try:
    engine = get_connection()

    with engine.connect() as connection:
        connection.execute(text("SELECT 1"))

except Exception as exc:
    st.error(
        "Unable to connect to MySQL. Check that the MySQL server "
        "is running and that `.streamlit/secrets.toml` contains "
        "the correct connection details."
    )

    st.exception(exc)
    st.stop()


# ============================================================
# 5. SHARED SOLAR KPI DATA
# ============================================================
plant1_kpi = read_query(
    """
    SELECT
        COUNT(*) AS total_records,
        ROUND(AVG(AC_POWER), 2) AS average_ac_power,
        ROUND(MAX(AC_POWER), 2) AS maximum_ac_power
    FROM plant1_solar
    """,
    engine,
).iloc[0]

plant2_kpi = read_query(
    """
    SELECT
        COUNT(*) AS total_records,
        ROUND(AVG(AC_POWER), 2) AS average_ac_power,
        ROUND(MAX(AC_POWER), 2) AS maximum_ac_power
    FROM plant2_solar
    """,
    engine,
).iloc[0]


# ============================================================
# 6. OVERVIEW
# ============================================================
if selected_page == "Overview":

    page_heading(
        "Project Overview",
        "A high-level view of the two solar plants and the analysis available in this dashboard.",
    )

    st.success(
        "Connected to the SolarPulse MySQL database.",
        icon="✅",
    )

    st.subheader("Solar generation snapshot")

    p1, p2 = st.columns(2)

    with p1:
        st.markdown("### Plant 1")

        c1, c2, c3 = st.columns(3)

        c1.metric(
            "Records",
            f"{int(plant1_kpi['total_records']):,}",
        )

        c2.metric(
            "Average AC power",
            f"{plant1_kpi['average_ac_power']:,.2f} kW",
        )

        c3.metric(
            "Maximum AC power",
            f"{plant1_kpi['maximum_ac_power']:,.2f} kW",
        )

    with p2:
        st.markdown("### Plant 2")

        c1, c2, c3 = st.columns(3)

        c1.metric(
            "Records",
            f"{int(plant2_kpi['total_records']):,}",
        )

        c2.metric(
            "Average AC power",
            f"{plant2_kpi['average_ac_power']:,.2f} kW",
        )

        c3.metric(
            "Maximum AC power",
            f"{plant2_kpi['maximum_ac_power']:,.2f} kW",
        )

    st.caption(
        "These KPIs cover the complete solar datasets. Average AC power "
        "includes nighttime zero readings and represents inverter-level observations."
    )

    st.divider()
    st.subheader("Explore the dashboard")

    cards = st.columns(3)

    overview_cards = [
        (
            "☀️ Solar Generation",
            "Compare observed AC power across both plants.",
        ),
        (
            "🌡️ Weather Analysis",
            "Explore ambient temperature, module temperature and irradiation.",
        ),
        (
            "🏠 Household Consumption",
            "Review daily and hourly active-power patterns in a separate French household dataset.",
        ),
        (
            "🧮 SQL Reports",
            "Explore five prepared reports powered by MySQL queries.",
        ),
        (
            "📊 Business Insights",
            "Review findings and practical recommendations.",
        ),
        (
            "🔎 Data Quality",
            "Understand coverage, missing observations and interpretation limits.",
        ),
    ]

    for index, (title, description) in enumerate(overview_cards):
        with cards[index % 3]:
            st.markdown(
                f"""
                <div class="insight-card">
                    <h3>{title}</h3>
                    <div>{description}</div>
                </div>
                """,
                unsafe_allow_html=True,
            )


# ============================================================
# 7. SOLAR GENERATION
# ============================================================
elif selected_page == "Solar Generation":

    page_heading(
        "Solar Generation",
        "Compare observed inverter-level AC power across the two solar plants.",
    )

    params = date_filter(
        engine,
        "plant1_solar",
        "Solar analysis",
        "solar",
    )

    if params:

        comparison_query = """
            SELECT
                p1.DATE_TIME,
                p1.plant1_total_ac_power,
                p2.plant2_total_ac_power
            FROM (
                SELECT
                    DATE_TIME,
                    SUM(AC_POWER) AS plant1_total_ac_power
                FROM plant1_solar
                WHERE DATE_TIME >= :start_date
                  AND DATE_TIME < DATE_ADD(:end_date, INTERVAL 1 DAY)
                GROUP BY DATE_TIME
            ) AS p1
            INNER JOIN (
                SELECT
                    DATE_TIME,
                    SUM(AC_POWER) AS plant2_total_ac_power
                FROM plant2_solar
                WHERE DATE_TIME >= :start_date
                  AND DATE_TIME < DATE_ADD(:end_date, INTERVAL 1 DAY)
                GROUP BY DATE_TIME
            ) AS p2
                ON p1.DATE_TIME = p2.DATE_TIME
            ORDER BY p1.DATE_TIME
        """

        comparison_df = read_query(
            comparison_query,
            engine,
            params,
        )

        if not comparison_df.empty:

            st.metric(
                "Common timestamps",
                f"{len(comparison_df):,}",
            )

            fig = px.line(
                comparison_df,
                x="DATE_TIME",
                y=[
                    "plant1_total_ac_power",
                    "plant2_total_ac_power",
                ],
                labels={
                    "DATE_TIME": "Date and time",
                    "value": "Aggregated AC power (kW)",
                    "variable": "Plant",
                },
                title="Observed AC Power — Plant 1 vs Plant 2",
                color_discrete_sequence=[
                    "#16856b",
                    "#e59b32",
                ],
            )

            fig = chart_layout(
                fig,
                "Aggregated AC power (kW)",
            )

            fig.update_layout(
                legend=dict(
                    orientation="h",
                    y=1.12,
                    x=0,
                )
            )

            st.plotly_chart(
                fig,
                use_container_width=True,
            )

            st.caption(
                f"Showing {len(comparison_df):,} timestamps present "
                "in both plant datasets for the selected period."
            )

        else:
            st.warning(
                "No common generation timestamps were found for the selected dates."
            )

        st.info(
            "Plant totals are sums of inverter-level power readings at each timestamp. "
            "Incomplete inverter reporting can affect comparisons; differences should "
            "not automatically be interpreted as differences in efficiency."
        )


# ============================================================
# 8. WEATHER ANALYSIS
# ============================================================
elif selected_page == "Weather Analysis":

    page_heading(
        "Weather Analysis",
        "Explore plant-level weather measurements and compare their patterns across the solar plants.",
    )

    params = date_filter(
        engine,
        "plant1_solar",
        "Weather analysis",
        "weather",
    )

    if params:

        weather_query = """
            SELECT DISTINCT
                'Plant 1' AS plant,
                DATE_TIME,
                AMBIENT_TEMPERATURE,
                MODULE_TEMPERATURE,
                IRRADIATION
            FROM plant1_solar
            WHERE DATE_TIME >= :start_date
              AND DATE_TIME < DATE_ADD(:end_date, INTERVAL 1 DAY)
              AND AMBIENT_TEMPERATURE IS NOT NULL

            UNION ALL

            SELECT DISTINCT
                'Plant 2' AS plant,
                DATE_TIME,
                AMBIENT_TEMPERATURE,
                MODULE_TEMPERATURE,
                IRRADIATION
            FROM plant2_solar
            WHERE DATE_TIME >= :start_date
              AND DATE_TIME < DATE_ADD(:end_date, INTERVAL 1 DAY)
              AND AMBIENT_TEMPERATURE IS NOT NULL

            ORDER BY DATE_TIME
        """

        weather_df = read_query(
            weather_query,
            engine,
            params,
        )

        if not weather_df.empty:

            weather_options = {
                "Ambient Temperature": (
                    "AMBIENT_TEMPERATURE",
                    "Temperature (°C)",
                ),
                "Module Temperature": (
                    "MODULE_TEMPERATURE",
                    "Temperature (°C)",
                ),
                "Solar Irradiation": (
                    "IRRADIATION",
                    "Irradiation",
                ),
            }

            selected_weather = st.selectbox(
                "Weather measurement",
                list(weather_options.keys()),
            )

            selected_column, y_label = weather_options[
                selected_weather
            ]

            fig = px.line(
                weather_df,
                x="DATE_TIME",
                y=selected_column,
                color="plant",
                labels={
                    "DATE_TIME": "Date and time",
                    selected_column: y_label,
                    "plant": "Solar plant",
                },
                title=f"{selected_weather} Over Time",
                color_discrete_sequence=[
                    "#16856b",
                    "#e59b32",
                ],
            )

            fig = chart_layout(fig, y_label)

            fig.update_layout(
                legend=dict(
                    orientation="h",
                    y=1.12,
                    x=0,
                )
            )

            st.plotly_chart(
                fig,
                use_container_width=True,
            )

            summary = (
                weather_df.groupby("plant")
                .agg(
                    average_ambient_temperature=(
                        "AMBIENT_TEMPERATURE",
                        "mean",
                    ),
                    average_module_temperature=(
                        "MODULE_TEMPERATURE",
                        "mean",
                    ),
                    average_irradiation=(
                        "IRRADIATION",
                        "mean",
                    ),
                    weather_observations=(
                        "DATE_TIME",
                        "count",
                    ),
                )
                .round(3)
                .reset_index()
            )

            st.subheader("Weather Statistics")

            st.dataframe(
                summary,
                use_container_width=True,
                hide_index=True,
            )

            st.caption(
                "Weather values are plant-level observations. Repeated weather "
                "values across inverter records are deduplicated for this view."
            )

        else:
            st.warning(
                "No weather observations were found for the selected dates."
            )


# ============================================================
# 9. HOUSEHOLD CONSUMPTION
# ============================================================
elif selected_page == "Household Consumption":

    page_heading(
        "Household Electricity Consumption",
        "Analyze daily and hourly active-power patterns in the individual household dataset.",
    )

    st.warning(
        "This is a separate dataset for one household in France, covering "
        "December 2006 to November 2010. It is not directly matched to the Indian solar plants."
    )

    params = date_filter(
        engine,
        "household_consumption",
        "Consumption analysis",
        "consumption",
    )

    if params:

        kpi_query = """
            SELECT
                COUNT(*) AS total_records,
                ROUND(AVG(Global_active_power), 3) AS average_active_power,
                ROUND(MAX(Global_active_power), 3) AS maximum_active_power
            FROM household_consumption
            WHERE DATE_TIME >= :start_date
              AND DATE_TIME < DATE_ADD(:end_date, INTERVAL 1 DAY)
        """

        kpi = read_query(
            kpi_query,
            engine,
            params,
        ).iloc[0]

        st.subheader("Consumption KPIs")

        a, b, c = st.columns(3)

        a.metric(
            "Records",
            f"{int(kpi['total_records']):,}",
        )

        b.metric(
            "Average active power",
            f"{kpi['average_active_power']:,.3f} kW",
        )

        c.metric(
            "Maximum active power",
            f"{kpi['maximum_active_power']:,.3f} kW",
        )

        daily_query = """
            SELECT
                DATE(DATE_TIME) AS consumption_date,
                ROUND(AVG(Global_active_power), 3) AS average_active_power,
                ROUND(MAX(Global_active_power), 3) AS maximum_active_power
            FROM household_consumption
            WHERE DATE_TIME >= :start_date
              AND DATE_TIME < DATE_ADD(:end_date, INTERVAL 1 DAY)
            GROUP BY DATE(DATE_TIME)
            ORDER BY consumption_date
        """

        daily_df = read_query(
            daily_query,
            engine,
            params,
        )

        if not daily_df.empty:

            daily_fig = px.line(
                daily_df,
                x="consumption_date",
                y="average_active_power",
                title="Daily Average Household Active Power",
                labels={
                    "consumption_date": "Date",
                    "average_active_power": "Average active power (kW)",
                },
                color_discrete_sequence=["#16856b"],
            )

            st.plotly_chart(
                chart_layout(
                    daily_fig,
                    "Average active power (kW)",
                ),
                use_container_width=True,
            )

        hourly_query = """
            SELECT
                HOUR(DATE_TIME) AS consumption_hour,
                COUNT(*) AS observations,
                ROUND(AVG(Global_active_power), 3) AS average_active_power,
                ROUND(MAX(Global_active_power), 3) AS maximum_active_power
            FROM household_consumption
            WHERE DATE_TIME >= :start_date
              AND DATE_TIME < DATE_ADD(:end_date, INTERVAL 1 DAY)
            GROUP BY HOUR(DATE_TIME)
            ORDER BY consumption_hour
        """

        hourly_df = read_query(
            hourly_query,
            engine,
            params,
        )

        if not hourly_df.empty:

            hourly_fig = px.bar(
                hourly_df,
                x="consumption_hour",
                y="average_active_power",
                title="Average Household Active Power by Hour",
                labels={
                    "consumption_hour": "Hour of day",
                    "average_active_power": "Average active power (kW)",
                },
                color="average_active_power",
                color_continuous_scale=[
                    "#d9eee7",
                    "#16856b",
                ],
            )

            hourly_fig.update_xaxes(
                tickmode="linear",
                dtick=1,
            )

            st.plotly_chart(
                chart_layout(
                    hourly_fig,
                    "Average active power (kW)",
                ),
                use_container_width=True,
            )

        st.info(
            "Active power is measured in kW, not energy in kWh. Because the household "
            "data is from a different country and period, it cannot be used to calculate "
            "solar self-consumption, solar surplus or grid dependency for these plants."
        )


# ============================================================
# 10. SQL REPORTS
# ============================================================
elif selected_page == "SQL Reports":

    page_heading(
        "SQL Reports",
        "Explore prepared MySQL reports. Each report runs against the selected analysis period.",
    )

    report = st.selectbox(
        "Choose a report",
        [
            "Daily Solar Generation Summary",
            "Top 5 Solar Inverters",
            "Plant-wise Generation Statistics",
            "Hourly Household Power Pattern",
            "Weather Data Availability",
        ],
    )

    if report in [
        "Daily Solar Generation Summary",
        "Top 5 Solar Inverters",
        "Plant-wise Generation Statistics",
        "Weather Data Availability",
    ]:
        solar_params = date_filter(
            engine,
            "plant1_solar",
            "Solar report",
            "sql_solar",
        )
    else:
        solar_params = None

    if report == "Daily Solar Generation Summary" and solar_params:

        plant = st.selectbox(
            "Choose solar plant",
            ["Plant 1", "Plant 2"],
            key="report_daily_plant",
        )

        table = (
            "plant1_solar"
            if plant == "Plant 1"
            else "plant2_solar"
        )

        query = f"""
            SELECT
                DATE(DATE_TIME) AS generation_date,
                COUNT(*) AS inverter_records,
                ROUND(AVG(AC_POWER), 2) AS average_ac_power,
                ROUND(MAX(AC_POWER), 2) AS maximum_ac_power,
                ROUND(SUM(AC_POWER), 2) AS sum_of_inverter_power_readings
            FROM {table}
            WHERE DATE_TIME >= :start_date
              AND DATE_TIME < DATE_ADD(:end_date, INTERVAL 1 DAY)
            GROUP BY DATE(DATE_TIME)
            ORDER BY generation_date
        """

        result = read_query(
            query,
            engine,
            solar_params,
        )

        st.dataframe(
            result,
            use_container_width=True,
            hide_index=True,
        )

        st.caption(
            "The sum of inverter power readings is not daily energy. "
            "Daily energy requires integration over valid time intervals."
        )

    elif report == "Top 5 Solar Inverters" and solar_params:

        plant = st.selectbox(
            "Choose solar plant",
            ["Plant 1", "Plant 2"],
            key="report_top_plant",
        )

        table = (
            "plant1_solar"
            if plant == "Plant 1"
            else "plant2_solar"
        )

        query = f"""
            SELECT
                SOURCE_KEY_GEN AS inverter_id,
                COUNT(*) AS observations,
                ROUND(AVG(AC_POWER), 2) AS average_ac_power,
                ROUND(MAX(AC_POWER), 2) AS maximum_ac_power
            FROM {table}
            WHERE DATE_TIME >= :start_date
              AND DATE_TIME < DATE_ADD(:end_date, INTERVAL 1 DAY)
              AND IRRADIATION > 0.05
            GROUP BY SOURCE_KEY_GEN
            ORDER BY average_ac_power DESC
            LIMIT 5
        """

        st.dataframe(
            read_query(query, engine, solar_params),
            use_container_width=True,
            hide_index=True,
        )

        st.caption(
            "Ranking is based on average AC power when irradiation exceeds 0.05. "
            "It is not an inverter-efficiency ranking."
        )

    elif report == "Plant-wise Generation Statistics" and solar_params:

        query = """
            SELECT
                'Plant 1' AS plant,
                COUNT(*) AS total_records,
                COUNT(DISTINCT SOURCE_KEY_GEN) AS inverter_count,
                ROUND(AVG(AC_POWER), 2) AS average_ac_power,
                ROUND(MAX(AC_POWER), 2) AS maximum_ac_power
            FROM plant1_solar
            WHERE DATE_TIME >= :start_date
              AND DATE_TIME < DATE_ADD(:end_date, INTERVAL 1 DAY)

            UNION ALL

            SELECT
                'Plant 2' AS plant,
                COUNT(*) AS total_records,
                COUNT(DISTINCT SOURCE_KEY_GEN) AS inverter_count,
                ROUND(AVG(AC_POWER), 2) AS average_ac_power,
                ROUND(MAX(AC_POWER), 2) AS maximum_ac_power
            FROM plant2_solar
            WHERE DATE_TIME >= :start_date
              AND DATE_TIME < DATE_ADD(:end_date, INTERVAL 1 DAY)
        """

        st.dataframe(
            read_query(query, engine, solar_params),
            use_container_width=True,
            hide_index=True,
        )

        st.caption(
            "Average AC power includes nighttime zero readings and may be "
            "affected by incomplete inverter reporting."
        )

    elif report == "Hourly Household Power Pattern":

        household_params = date_filter(
            engine,
            "household_consumption",
            "Household report",
            "sql_household",
        )

        if household_params:

            query = """
                SELECT
                    HOUR(DATE_TIME) AS hour_of_day,
                    COUNT(*) AS observations,
                    ROUND(AVG(Global_active_power), 3) AS average_active_power,
                    ROUND(MAX(Global_active_power), 3) AS maximum_active_power
                FROM household_consumption
                WHERE DATE_TIME >= :start_date
                  AND DATE_TIME < DATE_ADD(:end_date, INTERVAL 1 DAY)
                GROUP BY HOUR(DATE_TIME)
                ORDER BY hour_of_day
            """

            st.dataframe(
                read_query(
                    query,
                    engine,
                    household_params,
                ),
                use_container_width=True,
                hide_index=True,
            )

            st.caption(
                "This report uses the selected household date range, "
                "not the solar plant date range."
            )

    elif report == "Weather Data Availability" and solar_params:

        query = """
            SELECT
                'Plant 1' AS plant,
                COUNT(*) AS generation_records,
                SUM(
                    CASE
                        WHEN AMBIENT_TEMPERATURE IS NOT NULL THEN 1
                        ELSE 0
                    END
                ) AS records_with_weather,
                SUM(
                    CASE
                        WHEN AMBIENT_TEMPERATURE IS NULL THEN 1
                        ELSE 0
                    END
                ) AS records_without_weather
            FROM plant1_solar
            WHERE DATE_TIME >= :start_date
              AND DATE_TIME < DATE_ADD(:end_date, INTERVAL 1 DAY)

            UNION ALL

            SELECT
                'Plant 2' AS plant,
                COUNT(*) AS generation_records,
                SUM(
                    CASE
                        WHEN AMBIENT_TEMPERATURE IS NOT NULL THEN 1
                        ELSE 0
                    END
                ) AS records_with_weather,
                SUM(
                    CASE
                        WHEN AMBIENT_TEMPERATURE IS NULL THEN 1
                        ELSE 0
                    END
                ) AS records_without_weather
            FROM plant2_solar
            WHERE DATE_TIME >= :start_date
              AND DATE_TIME < DATE_ADD(:end_date, INTERVAL 1 DAY)
        """

        st.dataframe(
            read_query(query, engine, solar_params),
            use_container_width=True,
            hide_index=True,
        )


# ============================================================
# 11. BUSINESS INSIGHTS
# ============================================================
elif selected_page == "Business Insights":

    page_heading(
        "Business Insights & Recommendations",
        "Key findings from the analysis, with practical interpretation and recommended actions.",
    )

    insight_data = [
        (
            "1. Solar irradiation and power generation",
            "Solar irradiation showed the strongest positive correlation with AC power among the weather variables examined for both plants.",
            "Monitor irradiation alongside AC power to identify periods when generation is lower than expected.",
        ),
        (
            "2. Plant generation comparison",
            "On timestamps where all 22 inverters were reporting at both plants, Plant 1 had approximately 25.3% higher average observed AC power than Plant 2 in the analyzed complete-data sample.",
            "Investigate installed capacity, equipment configuration, operating conditions and inverter reporting before drawing conclusions about plant performance.",
        ),
        (
            "3. Inverter reporting and data quality",
            "Plant 2 had periods of incomplete inverter reporting, particularly during parts of May 21–28, 2020.",
            "Introduce automated monitoring for missing inverter records and investigate communication or data-collection interruptions.",
        ),
        (
            "4. Household electricity usage",
            "In the separate household dataset, average active power was highest around 8 PM (approximately 1.899 kW) and lowest around 4 AM (approximately 0.444 kW) over the analyzed full period.",
            "Time-of-day consumption patterns can inform household energy awareness and demand-management strategies.",
        ),
    ]

    for title, finding, recommendation in insight_data:

        st.markdown(
            f"""
            <div class="insight-card">
                <h3>{title}</h3>
                <b>Finding</b><br>
                {finding}
                <br><br>
                <b>Recommendation</b><br>
                {recommendation}
            </div>
            """,
            unsafe_allow_html=True,
        )

    st.warning(
        "Solar generation data is from two Indian plants in May–June 2020. "
        "Household consumption data is from one French household in 2006–2010. "
        "They cannot be combined to calculate actual solar self-consumption, "
        "solar surplus, grid imports or grid dependency."
    )

    st.caption(
        "The 25.3% result is a comparison of observed power in a complete-inverter "
        "sample, not a measure of plant efficiency. Correlation does not establish causation."
    )


# ============================================================
# 12. DATA QUALITY & LIMITATIONS
# ============================================================
elif selected_page == "Data Quality":

    page_heading(
        "Data Quality & Project Notes",
        "Important observations and limitations to keep in mind when interpreting the dashboard.",
    )

    left, right = st.columns(2)

    with left:

        st.markdown("### Solar generation")

        st.markdown(
            "- Generation readings are inverter-level observations.\n"
            "- Plant comparisons can be affected by incomplete inverter reporting.\n"
            "- Plant 1 has four generation records without matching weather readings.\n"
            "- Plant 2 `TOTAL_YIELD` contains anomalous values and is not used as the basis for energy estimates."
        )

        st.markdown("### Weather")

        st.markdown(
            "- Weather measurements are plant-level observations.\n"
            "- Repeated weather values across inverter records are deduplicated in the weather view."
        )

    with right:

        st.markdown("### Household consumption")

        st.markdown(
            "- The dataset represents one household in France.\n"
            "- Active power is measured in kW, not energy in kWh.\n"
            "- The household data is not directly matched to the Indian solar plant datasets."
        )

        st.markdown("### Interpretation")

        st.markdown(
            "- AC power is power, not energy. Energy in kWh requires integration over time.\n"
            "- Incomplete timestamps should not be treated as complete plant totals.\n"
            "- Correlation does not prove causation.\n"
            "- Observed power differences do not establish differences in efficiency."
        )

    st.divider()

    st.info(
        "For this project, the solar and household datasets are intentionally "
        "analyzed separately because they differ in geography and time period."
    )


# ============================================================
# 13. FOOTER
# ============================================================
st.divider()

st.markdown(
    """
    <div style="text-align:center; color:#64748b; font-size:.85rem;">
        Solar Analytics and Energy Insights · Data Analytics Capstone Project
        <br>
        Built with Python, MySQL, SQL, Plotly and Streamlit
    </div>
    """,
    unsafe_allow_html=True,
)
