from fastapi import FastAPI, HTTPException
from functools import lru_cache
from typing import List
from datetime import date
from database import get_snowflake_connection, get_mongo_collection
from functools import lru_cache  
import pandas as pd  
from prophet import Prophet  
from sklearn.cluster import KMeans  
from sklearn.preprocessing import StandardScaler  
import numpy as np

from models import CountyProfile, CountyListItem, CountyRankingItem
from models import CountyClusterData, CovidWave, TimeSeriesDataPoint, SnowflakeData, MongoDbContext
from models import ForecastDataPoint, ClusterProfile, ClusterInfo

app = FastAPI(
    title="COVID-19 County Analysis API",
    description="API for getting COVID-19 analytics data at the US county level.",
    version="1.0.0"
)

# --- Endpoint A: Detailed county profile ---
@app.get("/api/v1/county/{fips}", response_model=CountyProfile)
def get_county_profile(fips: str):
    """
    Gets a complete county profile by combining data from Snowflake and MongoDB.
    """
    # 1. Query Snowflake
    snowflake_conn = get_snowflake_connection()
    if not snowflake_conn:
        raise HTTPException(status_code=500, detail="Could not connect to Snowflake")

    # IMPORTANT: We use full table names including databases
    sql_query = f"""
        SELECT
            nyt.FIPS,
            nyt.COUNTY,
            nyt.STATE,
            MAX(nyt.CASES) AS Total_Cases,
            MAX(nyt.DEATHS) AS Total_Deaths,
            MAX(county.POPULATION) AS Population,
            MAX(county.PCT_CHILDREN_IN_POVERTY) AS Pct_Poverty,
            MAX(county.PCT_ADULTS_WITH_OBESITY) AS Pct_Obesity
        FROM "COVID_DB"."PUBLIC"."NYT_US_COVID19_OPTIMIZED" AS nyt
        JOIN "COVID_DB"."PUBLIC"."COUNTY_RANKED_MEASURE_DATA_2020_OPTIMIZED" AS county
            ON nyt.FIPS = county.FIPS
        WHERE nyt.FIPS = '{fips}'
        GROUP BY 1, 2, 3;
    """

    try:
        cursor = snowflake_conn.cursor()
        cursor.execute(sql_query)
        result = cursor.fetchone()
        if not result:
            raise HTTPException(status_code=404, detail=f"County with FIPS {fips} not found in Snowflake.")

        # Calculate on-the-fly
        population = result[5] if result[5] else 0
        total_deaths = result[4] if result[4] else 0
        deaths_per_100k = (total_deaths / population) * 100000 if population > 0 else 0

        snowflake_data = SnowflakeData(
            total_cases=result[3],
            total_deaths=total_deaths,
            population=population,
            deaths_per_100k=round(deaths_per_100k, 2),
            percent_children_in_poverty=result[6],
            percent_adults_with_obesity=result[7]
        )
    finally:
        cursor.close()
        snowflake_conn.close()

    # 2. Query MongoDB
    mongo_collection = get_mongo_collection()
    mongo_context_data = MongoDbContext() # Default empty
    if mongo_collection is not None:
        mongo_doc = mongo_collection.find_one({"_id": fips})
        if mongo_doc:
            mongo_context_data = MongoDbContext(
                annotations=mongo_doc.get("annotations", []),
                comments=mongo_doc.get("comments", []),
                external_sources=mongo_doc.get("externalSources", [])
            )

    # 3. Combine and return result
    return CountyProfile(
        fips=result[0],
        county_name=result[1],
        state=result[2],
        snowflake_data=snowflake_data,
        mongo_db_context=mongo_context_data
    )

# --- Endpoint B: List of all counties ---
@app.get("/api/v1/counties", response_model=List[CountyListItem])
@lru_cache(maxsize=None)
def get_county_list():
    """
    Returns a list of all available counties for use in the UI.
    """
    
    # This line is needed for testing  
    print("CACHE MISS: Running actual query to Snowflake for /api/v1/counties...")
    
    snowflake_conn = get_snowflake_connection()
    if not snowflake_conn:
        raise HTTPException(status_code=500, detail="Could not connect to Snowflake")

    sql_query = 'SELECT FIPS, COUNTY, STATE FROM "COVID_DB"."PUBLIC"."COUNTY_RANKED_MEASURE_DATA_2020_OPTIMIZED" WHERE COUNTY IS NOT NULL ORDER BY STATE, COUNTY;'

    try:
        cursor = snowflake_conn.cursor()
        cursor.execute(sql_query)
        results = cursor.fetchall()
        return [CountyListItem(fips=row[0], county_name=row[1], state=row[2]) for row in results]
    finally:
        cursor.close()
        snowflake_conn.close()
        
        
# --- New endpoint: Time series for county ---  
@app.get("/api/v1/county/{fips}/timeseries", response_model=List[TimeSeriesDataPoint])  
def get_county_timeseries(fips: str):  
    """  
    Returns time series data for cases and deaths for the specified county.  
    """  
    sql_query = f"""  
        SELECT  
            DATE,  
            CASES,  
            DEATHS  
        FROM "COVID_DB"."PUBLIC"."NYT_US_COVID19_OPTIMIZED"  
        WHERE FIPS = '{fips}'  
        ORDER BY DATE;  
    """  
    snowflake_conn = get_snowflake_connection()  
    if not snowflake_conn:  
        raise HTTPException(status_code=500, detail="Could not connect to Snowflake")  
  
    try:  
        cursor = snowflake_conn.cursor()  
        cursor.execute(sql_query)  
        results = cursor.fetchall()  
        if not results:  
            raise HTTPException(status_code=404, detail=f"Time series data not found for FIPS {fips}.")  
          
        return [TimeSeriesDataPoint(date=row[0], cases=row[1], deaths=row[2]) for row in results]  
    finally:  
        cursor.close()  
        snowflake_conn.close()

# --- Endpoint C: County rankings (simplified version) ---
# NOTE: Full implementation would require more complex SQL
@app.get("/api/v1/rankings", response_model=List[CountyRankingItem])
@lru_cache(maxsize=None)
def get_county_rankings():
    """
    Returns top 10 counties with the highest death rate per 100k population.
    """
    
    # This line is needed for testing  
    print("CACHE MISS: Running actual query to Snowflake for /api/v1/rankings...")
    
    # This query can be significantly optimized in Task 7
    sql_query = """
        WITH CountyTotals AS (
            SELECT
                FIPS,
                MAX(DEATHS) as Total_Deaths
            FROM "COVID_DB"."PUBLIC"."NYT_US_COVID19_OPTIMIZED"
            GROUP BY FIPS
        )
        SELECT
            ct.FIPS,
            cr.COUNTY,
            cr.STATE,
            (ct.Total_Deaths / cr.POPULATION) * 100000 AS Deaths_Per_100k
        FROM CountyTotals ct
        JOIN "COVID_DB"."PUBLIC"."COUNTY_RANKED_MEASURE_DATA_2020_OPTIMIZED" cr ON ct.FIPS = cr.FIPS
        WHERE cr.POPULATION > 0 AND Deaths_Per_100k IS NOT NULL
        ORDER BY Deaths_Per_100k DESC
        LIMIT 10;
    """
    snowflake_conn = get_snowflake_connection()
    if not snowflake_conn:
        raise HTTPException(status_code=500, detail="Could not connect to Snowflake")

    try:
        cursor = snowflake_conn.cursor()
        cursor.execute(sql_query)
        results = cursor.fetchall()
        return [CountyRankingItem(fips=row[0], county_name=row[1], state=row[2], metric_value=round(row[3], 2)) for row in results]
    finally:
        cursor.close()
        snowflake_conn.close()
        
# --- New endpoint: Data for clustering ---  
@app.get("/api/v1/data_for_clustering", response_model=List[CountyClusterData])
@lru_cache(maxsize=None)
def get_data_for_clustering():  
    """  
    Returns aggregated data for all counties for analysis and clustering.  
    """
    # This line is needed for testing  
    print("CACHE MISS: Running actual query to Snowflake for /api/v1/data_for_clustering...")
    
    # This SQL query combines mortality data from NYT with demographic data  
    sql_query = """  
        WITH CountyTotals AS (  
            -- Step 1: Calculate total deaths for each county  
            SELECT  
                FIPS,  
                MAX(DEATHS) as Total_Deaths  
            FROM "COVID_DB"."PUBLIC"."NYT_US_COVID19_OPTIMIZED"  
            GROUP BY FIPS  
        )  
        -- Step 2: Join with main table and calculate metrics  
        SELECT  
            cr.FIPS,  
            cr.COUNTY,  
            cr.STATE,  
            (ct.Total_Deaths / cr.POPULATION) * 100000 AS Deaths_Per_100k,  
            cr.PCT_CHILDREN_IN_POVERTY,  
            cr.PCT_ADULTS_WITH_OBESITY,  
            cr.PCT_UNEMPLOYED  
        FROM "COVID_DB"."PUBLIC"."COUNTY_RANKED_MEASURE_DATA_2020_OPTIMIZED" cr  
        JOIN CountyTotals ct ON cr.FIPS = ct.FIPS  
        WHERE  
            cr.POPULATION > 1000 -- Exclude very small counties for stability  
            AND Deaths_Per_100k IS NOT NULL  
            AND cr.PCT_CHILDREN_IN_POVERTY IS NOT NULL  
            AND cr.PCT_ADULTS_WITH_OBESITY IS NOT NULL  
            AND cr.PCT_UNEMPLOYED IS NOT NULL;  
    """  
    snowflake_conn = get_snowflake_connection()  
    if not snowflake_conn:  
        raise HTTPException(status_code=500, detail="Could not connect to Snowflake")  
  
    try:  
        cursor = snowflake_conn.cursor()  
        cursor.execute(sql_query)  
        results = cursor.fetchall()  
          
        return [  
            CountyClusterData(  
                fips=row[0],  
                county_name=row[1],  
                state=row[2],  
                deaths_per_100k=row[3],  
                percent_children_in_poverty=row[4],  
                percent_adults_with_obesity=row[5],  
                percent_unemployed=row[6]  
            ) for row in results  
        ]  
    finally:  
        cursor.close()  
        snowflake_conn.close()

@app.get("/api/v1/county/{fips}/waves", response_model=List[CovidWave])  
def get_county_waves(fips: str):  
    """  
    Finds and returns all COVID 'waves' for the specified county  
    using MATCH_RECOGNIZE.  
    """  
    sql_query = f"""  
        WITH DailyCases AS (  
            SELECT  
                FIPS,  
                DATE,  
                CASES - LAG(CASES, 1, 0) OVER (PARTITION BY FIPS ORDER BY DATE) AS new_cases  
            FROM COVID_DB.PUBLIC.NYT_US_COVID19_OPTIMIZED  
            WHERE FIPS = '{fips}'  
        )  
        SELECT  
            wave_number,  
            wave_start_date,  
            wave_end_date,  
            peak_cases,  
            peak_date  
        FROM DailyCases  
        MATCH_RECOGNIZE (  
            PARTITION BY FIPS  
            ORDER BY DATE  
            MEASURES  
                MATCH_NUMBER() AS wave_number,  
                FIRST(DATE) AS wave_start_date,  
                LAST(DATE) AS wave_end_date,  
                MAX(new_cases) AS peak_cases,  
                LAST(UP.DATE) AS peak_date  
            ONE ROW PER MATCH  
            PATTERN (UP{{3,}} DOWN{{3,}})  
            DEFINE  
                UP AS new_cases > LAG(new_cases, 1, 0),  
                DOWN AS new_cases < LAG(new_cases, 1, 0)  
        )  
    """  
    snowflake_conn = get_snowflake_connection()  
    if not snowflake_conn:  
        raise HTTPException(status_code=500, detail="Could not connect to Snowflake")  
  
    try:  
        cursor = snowflake_conn.cursor()  
        cursor.execute(sql_query)  
        results = cursor.fetchall()  
          
        # Create list of CovidWave objects based on results  
        waves = []  
        for row in results:  
            wave_data = CovidWave(  
                wave_number=row[0],  
                wave_start_date=row[1],  
                wave_end_date=row[2],  
                peak_cases=row[3],  
                peak_date=row[4]  
            )  
            waves.append(wave_data)  
          
        return waves  
          
    except Exception as e:  
        # Add logging for future debugging  
        print(f"An error occurred: {e}")  
        raise HTTPException(status_code=500, detail="An error occurred while processing the request.")  
    finally:  
        if snowflake_conn:  
            cursor.close()  
            snowflake_conn.close()
            
# --- Endpoint: Time series forecasting ---  
@app.get("/api/v1/county/{fips}/forecast", response_model=List[ForecastDataPoint])  
def get_county_forecast(fips: str):  
    """  
    Builds and returns a 30-day forecast of new cases for the county.  
    """  
    # 1. Get historical data  
    ts_data = get_county_timeseries(fips) # Use our existing function  
    df = pd.DataFrame([vars(d) for d in ts_data])  
    df['new_cases'] = df['cases'].diff().fillna(0)  
    df = df[['date', 'new_cases']].rename(columns={'date': 'ds', 'new_cases': 'y'})  
    df = df[df['y'] >= 0] # Remove anomalies  
  
    # 2. Train Prophet model  
    model = Prophet()  
    model.fit(df)  
  
    # 3. Make forecast  
    future = model.make_future_dataframe(periods=30)  
    forecast = model.predict(future)  
  
    # 4. Return only needed data  
    result = forecast[['ds', 'yhat', 'yhat_lower', 'yhat_upper']].tail(30)  
    return [  
        ForecastDataPoint(  
            date=row.ds.date(),  
            prediction=row.yhat,  
            prediction_lower=row.yhat_lower,  
            prediction_upper=row.yhat_upper  
        ) for _, row in result.iterrows()  
    ]  
  
# --- Endpoint: Clustering all counties ---  
@app.get("/api/v1/clusters", response_model=List[ClusterInfo])  
@lru_cache(maxsize=None) # Cache result since clustering is expensive  
def get_clusters():  
    """  
    Performs clustering of all counties and returns cluster membership.  
    """  
    print("CACHE MISS: Running clustering...")  
    # 1. Get data  
    data = get_data_for_clustering() # Use existing function  
    df = pd.DataFrame([vars(d) for d in data])  
      
    # 2. Prepare data  
    features = ['deaths_per_100k', 'percent_children_in_poverty', 'percent_adults_with_obesity', 'percent_unemployed']  
    X = df[features]  
    scaler = StandardScaler()  
    X_scaled = scaler.fit_transform(X)  
  
    # 3. K-Means clustering  
    kmeans = KMeans(n_clusters=4, random_state=42, n_init=10)  
    df['cluster'] = kmeans.fit_predict(X_scaled)  
  
    return [ClusterInfo(fips=row.fips, cluster=row.cluster) for _, row in df.iterrows()]  
  
# --- Endpoint: Cluster profiles ---  
@app.get("/api/v1/clusters/profiles", response_model=List[ClusterProfile])  
@lru_cache(maxsize=None) # Also cache  
def get_cluster_profiles():  
    """  
    Returns calculated profiles (average values) for each cluster.  
    """  
    print("CACHE MISS: Calculating cluster profiles...")  
    # 1. Get data and clusters  
    data = get_data_for_clustering()  
    df = pd.DataFrame([vars(d) for d in data])  
    clusters = get_clusters()  
    clusters_df = pd.DataFrame([vars(c) for c in clusters])  
    df = pd.merge(df, clusters_df, on='fips')  
  
    # 2. Calculate profiles  
    profiles = df.groupby('cluster').agg(  
        count=('fips', 'count'),  
        deaths_per_100k=('deaths_per_100k', 'mean'),  
        percent_children_in_poverty=('percent_children_in_poverty', 'mean'),  
        percent_adults_with_obesity=('percent_adults_with_obesity', 'mean'),  
        percent_unemployed=('percent_unemployed', 'mean')  
    ).reset_index()  
  
    return [ClusterProfile(**row) for _, row in profiles.to_dict(orient='index').items()]