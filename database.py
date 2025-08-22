import os
import snowflake.connector
from pymongo import MongoClient
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# --- Snowflake Connection ---
def get_snowflake_connection():
    """Creates and returns a connection to Snowflake."""
    try:
        conn = snowflake.connector.connect(
            user=os.getenv("SNOWFLAKE_USER"),
            password=os.getenv("SNOWFLAKE_PASSWORD"),
            account=os.getenv("SNOWFLAKE_ACCOUNT"),
            warehouse=os.getenv("SNOWFLAKE_WAREHOUSE")
        )
        return conn
    except Exception as e:
        print(f"Error connecting to Snowflake: {e}")
        return None

def get_mongo_collection():
    """Creates a connection to MongoDB and returns the county_context collection."""
    try:
        client = MongoClient(os.getenv("MONGO_CONNECTION_STRING"))
        db = client['covid_db'] # My database name
        return db['county_context'] # My Your collection name
    except Exception as e:
        print(f"Error connecting to MongoDB: {e}")
        return None