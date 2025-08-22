# Comprehensive COVID-19 Analytics Platform

A full-featured web application for analyzing COVID-19 data across U.S. counties. Explore data interactively, build forecasts, cluster similar counties, and detect wave patterns in case dynamics.

## 🚀 Key Features

- 𝗜𝗻𝘁𝗲𝗿𝗮𝗰𝘁𝗶𝘃𝗲 𝗱𝗮𝘀𝗵𝗯𝗼𝗮𝗿𝗱 (Streamlit)
  - Single UI to access all analytics tools.
- 𝗔𝗱𝘃𝗮𝗻𝗰𝗲𝗱 𝗮𝗻𝗮𝗹𝘆𝘁𝗶𝗰𝘀
  - Time series forecasting with Prophet.
  - County clustering using K-Means on socio-economic and health indicators.
- 𝗣𝗮𝘁𝘁𝗲𝗿𝗻 𝗿𝗲𝗰𝗼𝗴𝗻𝗶𝘁𝗶𝗼𝗻
  - Wave detection with Snowflake MATCH_RECOGNIZE.
- 𝗣𝗲𝗿𝗳𝗼𝗿𝗺𝗮𝗻𝗰𝗲 𝗼𝗽𝘁𝗶𝗺𝗶𝘇𝗮𝘁𝗶𝗼𝗻
  - Clustered tables in Snowflake and API-level caching.
- 𝗦𝗰𝗮𝗹𝗮𝗯𝗹𝗲 𝗮𝗿𝗰𝗵𝗶𝘁𝗲𝗰𝘁𝘂𝗿𝗲
  - Clear split: FastAPI backend + Streamlit frontend.

## 🏛️ Architecture

Data Layer (Snowflake) 💾 ⟷ Backend / API (FastAPI) 🧠 ⟷ Frontend (Streamlit) 🖥️

- Data Layer (Snowflake): Optimized and clustered tables for fast queries.
- Backend (FastAPI): Business logic, SQL, ML execution, REST API.
- Presentation (Streamlit): Interactive UI fetching from API.

## ⚙️ Getting Started

### Prerequisites

- Python 3.8+
- Virtual environment (venv or conda)
- Snowflake account access

### Installation

```bash
git clone [YOUR REPO URL]
cd [YOUR PROJECT FOLDER]

python -m venv .venv
# macOS/Linux
source .venv/bin/activate
# Windows
# .venv\Scripts\activate

pip install -r requirements.txt
```

Create a `.env` file in the project root:

```
SNOWFLAKE_USER=YOUR_USERNAME
SNOWFLAKE_PASSWORD=YOUR_PASSWORD
SNOWFLAKE_ACCOUNT=YOUR_SNOWFLAKE_ACCOUNT
SNOWFLAKE_WAREHOUSE=COMPUTE_WH
SNOWFLAKE_DATABASE=COVID_DB
SNOWFLAKE_SCHEMA=PUBLIC
```

Ensure Snowflake has these optimized tables prepared:
- NYT_US_COVID19_OPTIMIZED
- COUNTY_RANKED_MEASURE_DATA_2020_OPTIMIZED

### Run

In two terminals:

Terminal 1 — API:
```bash
uvicorn main:app --reload
# Server at http://127.0.0.1:8000
```

Terminal 2 — Frontend:
```bash
streamlit run streamlit_app.py
# App at http://localhost:8501
```

## 📂 Project Structure

```
/
├── .venv/                  # Virtual environment
├── streamlit_app.py        # Streamlit frontend
├── main.py                 # FastAPI backend
├── models.py               # Pydantic data models
├── database.py             # Snowflake connection logic
├── requirements.txt        # Python dependencies
```

## 🌐 API Endpoints

- GET `/api/v1/counties` — List all counties
- GET `/api/v1/county/{fips}` — Detailed county profile
- GET `/api/v1/county/{fips}/timeseries` — County COVID-19 time series
- GET `/api/v1/county/{fips}/waves` — Detected pandemic “waves”
- GET `/api/v1/county/{fips}/forecast` — 30-day case forecast
- GET `/api/v1/clusters` — Cluster membership for each county
- GET `/api/v1/clusters/profiles` — Average profiles per cluster

## 📌 Notes

- Wave detection uses Snowflake’s MATCH_RECOGNIZE to identify sustained rises and falls.
- Forecasting uses Prophet; ensure the environment has the proper dependencies.
- Caching is applied at the API and Streamlit levels to improve responsiveness.
