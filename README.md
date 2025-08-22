Comprehensive COVID-19 Analytics Platform

This project is a full-featured web application for analyzing COVID-19 data in the United States. The platform lets you interactively explore county-level data, build forecasts, uncover hidden patterns with machine learning, and detect wave-like trends in case dynamics.

🚀 Key Features

Interactive dashboard: A single Streamlit interface to access all analytics tools.

Advanced analytics:

Time series forecasting using Prophet to predict future cases.

Cluster analysis with K-Means to segment counties by socio-economic and health indicators.

Pattern recognition: Automatic detection of pandemic "waves" using Snowflake's MATCH_RECOGNIZE.

Performance optimization: Fast responses thanks to clustered tables in Snowflake and API-level caching.

Scalable architecture: Clear separation of backend (FastAPI) and frontend (Streamlit) for reliability and easier development.

🏛️ Architecture

The project follows a three-tier architecture for clear separation of concerns and flexibility.

Data Layer (Snowflake) 💾 <--> Backend / API (FastAPI) 🧠 <--> Frontend (Streamlit) 🖥️


Data Layer (Snowflake): Stores optimized and clustered tables for fast access.

Backend Layer (FastAPI): Encapsulates business logic: SQL execution, ML model runs, and data exposure via REST API.

Presentation Layer (Streamlit): Interactive UI that fetches from the API and renders visualizations.

⚙️ Getting Started

Follow these steps to run the project locally.

Prerequisites

Python 3.8+

Virtual environment (venv or conda)

Access to a Snowflake account

Installation and Run
Clone the repository:
git clone [YOUR REPO URL]
cd [YOUR PROJECT FOLDER]

Create and activate a virtual environment:
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate

Install dependencies:
pip install -r requirements.txt

Set environment variables: Create a .env file in the project root with:
SNOWFLAKE_USER=YOUR_USERNAME
SNOWFLAKE_PASSWORD=YOUR_PASSWORD
SNOWFLAKE_ACCOUNT=YOUR_SNOWFLAKE_ACCOUNT
SNOWFLAKE_WAREHOUSE=COMPUTE_WH
SNOWFLAKE_DATABASE=COVID_DB
SNOWFLAKE_SCHEMA=PUBLIC


Prepare the database in Snowflake: Make sure you have created the optimized tables NYT_US_COVID19_OPTIMIZED and COUNTY_RANKED_MEASURE_DATA_2020_OPTIMIZED with clustering configured.

Start the application (in two terminals):

Terminal 1 — Start the API server:

uvicorn main:app --reload


Terminal 2 — Start the Streamlit app:

streamlit run streamlit_app.py


The API server will be available at http://127.0.0.1:8000 and the Streamlit app will open in your browser at http://localhost:8501.

📂 Project Structure
/
├── .venv/                  # Virtual environment
├── streamlit_app.py        # Streamlit frontend
├── main.py                 # FastAPI backend
├── models.py               # Pydantic data models for the API
├── database.py             # Snowflake connection logic
├── requirements.txt        # Python dependencies
└── .env                    # Secrets (do not commit)

🌐 API Endpoints

The backend provides the following core endpoints:

GET /api/v1/counties: Returns a list of all counties.

GET /api/v1/county/{fips}: Returns a detailed county profile.

GET /api/v1/county/{fips}/timeseries: Returns the COVID-19 time series for a county.

GET /api/v1/county/{fips}/waves: Detects and returns pandemic "waves".

GET /api/v1/county/{fips}/forecast: Builds and returns a 30-day case forecast.

GET /api/v1/clusters: Performs clustering and returns each county's cluster membership.

GET /api/v1/clusters/profiles: Returns average profiles for each cluster.

🔧 Technologies Used

Backend: FastAPI, Python

Frontend: Streamlit

Database: Snowflake

Machine Learning: Prophet (forecasting), scikit-learn (clustering)

Data Processing: pandas, numpy

Visualization: Plotly

📊 Features Overview
County Profiles

Get comprehensive information about any US county including population, COVID-19 statistics, and socio-economic indicators.

Time Series Analysis

View historical trends and detect patterns in case data over time.

Wave Detection

Automatically identify periods of sustained growth and decline in cases using advanced pattern matching.

Forecasting

Generate 30-day predictions for new cases using Facebook's Prophet algorithm.

Cluster Analysis

Discover groups of similar counties based on health outcomes and demographic factors.
