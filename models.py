from pydantic import BaseModel
from datetime import date
from typing import List, Optional, Any

# Models for the "County Profile" endpoint
class SnowflakeData(BaseModel):
    total_cases: int
    total_deaths: int
    population: int
    deaths_per_100k: float
    percent_children_in_poverty: Optional[float]
    percent_adults_with_obesity: Optional[float]

class MongoDbContext(BaseModel):
    # Metadata and user-provided context for a county
    annotations: List[Any] = []
    comments: List[Any] = []
    external_sources: List[Any] = []

class CountyProfile(BaseModel):
    # Combined profile from Snowflake metrics and MongoDB context
    fips: str
    county_name: str
    state: str
    snowflake_data: SnowflakeData
    mongo_db_context: MongoDbContext

# Model for the "County List" endpoint
class CountyListItem(BaseModel):
    fips: str
    county_name: str
    state: str

# Model for the "County Ranking" endpoint
class CountyRankingItem(BaseModel):
    fips: str
    county_name: str
    state: str
    metric_value: float

class TimeSeriesDataPoint(BaseModel):
    """One data point in a time series."""
    date: date
    cases: int
    deaths: int

class Annotation(BaseModel):
    """New annotation/comment payload."""
    text: str

class CountyClusterData(BaseModel):
    """Input features used for clustering counties."""
    fips: str
    county_name: str
    state: str
    deaths_per_100k: float | None = None
    percent_children_in_poverty: float | None = None
    percent_adults_with_obesity: float | None = None
    percent_unemployed: float | None = None

class CovidWave(BaseModel):
    """Summary of an identified COVID wave for a county/state."""
    wave_number: int
    wave_start_date: date
    wave_end_date: date
    peak_cases: int
    peak_date: date

class ForecastDataPoint(BaseModel):
    """Forecasted value and its confidence interval for a date."""
    date: date
    prediction: float
    prediction_lower: float
    prediction_upper: float

class ClusterInfo(BaseModel):
    """Cluster assignment for a county."""
    fips: str
    cluster: int

class ClusterProfile(BaseModel):
    """Aggregated profile/statistics for a cluster."""
    cluster: int
    count: int
    deaths_per_100k: float
    percent_children_in_poverty: float
    percent_adults_with_obesity: float
    percent_unemployed: float