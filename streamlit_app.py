import streamlit as st
import requests
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

# --- 1. PAGE SETTINGS AND API ---
st.set_page_config(
    page_title="Comprehensive COVID-19 Dashboard",
    page_icon="🦠",
    layout="wide"
)
API_BASE_URL = "http://127.0.0.1:8000/api/v1"

# --- 2. FUNCTIONS TO LOAD DATA FROM API ---
# Use Streamlit caching to speed things up
@st.cache_data
def get_api_data(endpoint):
    """Generic function to fetch data from the API."""
    try:
        response = requests.get(f"{API_BASE_URL}/{endpoint}")
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        st.error(f"Error connecting to API: {e}")
        return None

# --- 3. MAIN APP UI ---
st.title("📊 Comprehensive COVID-19 Analytics Dashboard (USA)")
st.markdown("A single app demonstrating all project features: from basic stats to forecasting and pattern detection.")

# --- Sidebar for county selection ---
st.sidebar.header("Control Panel")
counties = get_api_data("counties")

if counties:
    county_options = {f"{c['county_name']}, {c['state']}": c['fips'] for c in counties}
    selected_county_name = st.sidebar.selectbox(
        "Choose a county for analysis:",
        options=county_options.keys()
    )
    selected_fips = county_options[selected_county_name]

    st.header(f"Analysis for: {selected_county_name}")

    # --- Create tabs for different analysis sections ---
    tab_overview, tab_waves, tab_forecast, tab_cluster = st.tabs([
        "📈 Overview",
        "🌊 Wave Analysis",
        "🔮 Forecasting",
        "🧩 Cluster Analysis"
    ])

    # --- TAB 1: OVERVIEW ---
    with tab_overview:
        profile = get_api_data(f"county/{selected_fips}")
        if profile:
            st.subheader("Key Metrics")
            p_data = profile['snowflake_data']
            col1, col2, col3, col4 = st.columns(4)
            col1.metric("Population", f"{p_data['population']:,}")
            col2.metric("Total cases", f"{p_data['total_cases']:,}")
            col3.metric("Total deaths", f"{p_data['total_deaths']:,}")
            col4.metric("Deaths per 100k", f"{p_data['deaths_per_100k']:.1f}")

            st.subheader("Cases over time (daily new cases)")
            ts_data = get_api_data(f"county/{selected_fips}/timeseries")
            if ts_data:
                df = pd.DataFrame(ts_data)
                df['date'] = pd.to_datetime(df['date'])
                df['new_cases'] = df['cases'].diff().fillna(0).clip(lower=0)
                fig = px.line(df, x='date', y='new_cases', labels={'date': 'Date', 'new_cases': 'New cases'})
                st.plotly_chart(fig, use_container_width=True)

    # --- TAB 2: WAVE ANALYSIS ---
    with tab_waves:
        st.subheader("Detected pandemic waves")
        st.markdown("These are periods with steady growth in cases (3+ days) followed by a steady decline (3+ days).")
        
        waves_data = get_api_data(f"county/{selected_fips}/waves")
        ts_data = get_api_data(f"county/{selected_fips}/timeseries")

        if waves_data and ts_data:
            df = pd.DataFrame(ts_data)
            df['date'] = pd.to_datetime(df['date'])
            df['new_cases'] = df['cases'].diff().fillna(0).clip(lower=0)
            
            fig = px.line(
                df,
                x='date',
                y='new_cases',
                title="Daily new cases with highlighted waves",
                labels={'date': 'Date', 'new_cases': 'New cases'}
            )
            
            for wave in waves_data:
                fig.add_vrect(
                    x0=wave['wave_start_date'], x1=wave['wave_end_date'],
                    fillcolor="rgba(255,0,0,0.15)", line_width=0,
                    annotation_text=f"Wave #{wave['wave_number']}", annotation_position="top left"
                )
                fig.add_trace(go.Scatter(
                    x=[wave['peak_date']], y=[wave['peak_cases']],
                    mode='markers+text',
                    marker=dict(color='red', size=10, symbol='star'),
                    text=[f"Peak: {wave['peak_cases']:,}"],
                    textposition="top center",
                    name=f"Wave {wave['wave_number']} peak"
                ))
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("No clear waves found or not enough data for this county.")

    # --- TAB 3: FORECASTING ---  
    with tab_forecast:  
        st.subheader("30-day case forecast")  
        st.markdown("Click the button to train a Prophet model and build a forecast based on the full history.")  
  
        # view scale selector — placed before the button and stored in session_state
        st.markdown("---")
        if "view_option" not in st.session_state:
            st.session_state.view_option = "Full view"

        view_option = st.radio(
            "Choose chart scale:",
            options=["Full view", "Zoom to forecast"],
            horizontal=True,
            key="view_option",
        )

        if st.button("🚀 Build forecast"):  
            with st.spinner("Training the model and building the forecast... This may take up to a minute."):  
                # 1. Fetch all required data from the API  
                forecast_data = get_api_data(f"county/{selected_fips}/forecast")  
                ts_data = get_api_data(f"county/{selected_fips}/timeseries")  
  
            if forecast_data and ts_data:  
                # 2. Prepare dataframes  
                hist_df = pd.DataFrame(ts_data)  
                hist_df['date'] = pd.to_datetime(hist_df['date'])  
                hist_df['new_cases'] = hist_df['cases'].diff().fillna(0).clip(lower=0)  
                  
                fcst_df = pd.DataFrame(forecast_data)  
                fcst_df['date'] = pd.to_datetime(fcst_df['date'])  
  
                # 3. Build the base chart (always the same)  
                fig = go.Figure()  
                # Layer with historical data  
                fig.add_trace(go.Scatter(
                    x=hist_df['date'], y=hist_df['new_cases'],
                    mode='lines', name='Historical data',
                    line=dict(color='royalblue')
                ))  
                # Layer with forecast line  
                fig.add_trace(go.Scatter(
                    x=fcst_df['date'], y=fcst_df['prediction'],
                    mode='lines', name='Forecast',
                    line=dict(color='red', dash='dash')
                ))  
                # Layer with confidence interval (upper and lower bounds)  
                fig.add_trace(go.Scatter(  
                    x=pd.concat([fcst_df['date'], fcst_df['date'][::-1]]),  # x for fill  
                    y=pd.concat([fcst_df['prediction_upper'], fcst_df['prediction_lower'][::-1]]),  # y for fill  
                    fill='toself',  
                    fillcolor='rgba(255,0,0,0.2)',  
                    line=dict(color='rgba(255,255,255,0)'),  
                    hoverinfo="skip",  
                    name='Confidence interval'  
                ))

                # Scale and title based on the selected option
                if st.session_state.view_option == "Zoom to forecast":
                    hist_end = hist_df['date'].max()
                    zoom_start_date = hist_end - pd.Timedelta(days=30)
                    zoom_end_date = max(fcst_df['date'].max(), hist_end)

                    fig.update_layout(
                        title_text="Zoomed-in 30-day forecast",
                        xaxis_range=[zoom_start_date, zoom_end_date]
                    )
                    fig.update_xaxes(type="date")
                else:
                    fig.update_layout(title_text="Historical data and forecast")
                    fig.update_xaxes(type="date")
  
                # 6. Show the configured chart  
                st.plotly_chart(fig, use_container_width=True)  
            else:  
                st.error("Could not build the forecast. There may be insufficient data for this county.")

    # --- TAB 4: CLUSTER ANALYSIS ---  
    with tab_cluster:  
        st.subheader("Similarity analysis with other counties")  
        with st.spinner("Loading clustering data..."):  
            clusters = get_api_data("clusters")  
        profiles = get_api_data("clusters/profiles")  
        all_data = get_api_data("data_for_clustering")  
  
        if clusters and profiles and all_data:  
            # --- DEFINE CLUSTER 'PERSONAS' ---  
            cluster_explanations = {  
                0: {  
                    "name": "Average counties",  
                    "description": "This group sits in the 'middle' with moderate values across metrics. Adult obesity is relatively high, reflecting a common national issue."  
                },  
                1: {  
                    "name": "Counties with health system strain",  
                    "description": "Key trait is high mortality that is not always paired with the worst socio-economic metrics. May indicate limited access to quality healthcare."  
                },  
                2: {  
                    "name": "Most advantaged",  
                    "description": "Counties with the lowest mortality, child poverty, obesity, and unemployment. These areas handled the pandemic impacts best."  
                },  
                3: {  
                    "name": "Counties in socio-economic crisis",  
                    "description": "Highest levels of poverty, obesity, and unemployment with very high mortality. These are the most vulnerable regions."  
                }  
            } 
  
            # Find the cluster for the selected county and add its name  
            county_cluster_num = next((c['cluster'] for c in clusters if c['fips'] == selected_fips), -1)  
            county_cluster_name = cluster_explanations.get(county_cluster_num, {}).get("name", "Unknown")  
              
            st.info(f"**This county belongs to cluster #{county_cluster_num}: “{county_cluster_name}”**")  
  
            # --- INTERACTIVE DESCRIPTIONS FOR ALL CLUSTERS ---  
            st.subheader("Cluster descriptions")  
              
            # Sort profiles by cluster number for consistency  
            sorted_profiles = sorted(profiles, key=lambda p: p['cluster'])  
  
            for profile in sorted_profiles:  
                cluster_num = profile['cluster']  
                name = cluster_explanations.get(cluster_num, {}).get("name", f"Cluster {cluster_num}")  
                description = cluster_explanations.get(cluster_num, {}).get("description", "")  
                  
                # Use st.expander for nice collapsible sections  
                with st.expander(f"**Cluster {cluster_num}: {name}** ({profile['count']} counties)"):  
                    st.markdown(f"_{description}_")  
                    st.markdown(f"""  
                    - **Average deaths per 100k:** `{profile['deaths_per_100k']:.1f}`  
                    - **Average % child poverty:** `{profile['percent_children_in_poverty']:.1f}%`  
                    - **Average % adult obesity:** `{profile['percent_adults_with_obesity']:.1f}%`  
                    - **Average % unemployment:** `{profile['percent_unemployed']:.1f}%`  
                    """) 
  
            # Visualize all clusters (scatter plot)
            st.subheader("Interactive cluster scatter")  
            df = pd.DataFrame(all_data)  
            clusters_df = pd.DataFrame(clusters)  
            df = pd.merge(df, clusters_df, on='fips')  
            df['cluster'] = df['cluster'].astype(str)  
            df['size'] = 5  
            df['text'] = df['county_name'] + ', ' + df['state'] + '<br>Cluster: ' + df['cluster']  
  
            st.info(  
                """  
                **Why is the default X-axis 'Child poverty'?**  
                This metric is a strong indicator of the overall socio-economic health of a region.  
                The chart shows a strong relationship between poverty levels and pandemic outcomes.  
                Use the dropdown below to explore other factors.  
                """  
            )  
  
            x_axis_options = {  
                "Child poverty, %": "percent_children_in_poverty",  
                "Adult obesity, %": "percent_adults_with_obesity",  
                "Unemployment, %": "percent_unemployed"  
            }  
  
            selected_label = st.selectbox(  
                "Choose a metric for the X-axis:",  
                options=list(x_axis_options.keys())  
            )  
            selected_column = x_axis_options[selected_label]  
  
            fig = px.scatter(  
                df,  
                x=selected_column,  
                y="deaths_per_100k",  
                color="cluster",  
                size='size',  
                hover_name='text',  
                labels={  
                    selected_column: selected_label,  
                    "deaths_per_100k": "Deaths per 100k population"  
                },  
                title=f"Deaths vs. {selected_label.split(',')[0]}"  
            )  
            st.plotly_chart(fig, use_container_width=True)

else:
    st.error("Failed to load county list from the API. Please make sure the FastAPI server is running at " + API_BASE_URL)