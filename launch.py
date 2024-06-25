import streamlit as st
import pandas as pd
import requests
import sqlite3
import matplotlib.pyplot as plt
import seaborn as sns
import re
import os
from datetime import datetime
import json

DATABASE_PATH = 'lehrgaenge_data.db'
FLAG_PATH = 'subprocess_ran.flag'

# Function to initialize the database
def initialize_database():
    conn = sqlite3.connect(DATABASE_PATH)
    c = conn.cursor()
    c.execute('''
        CREATE TABLE IF NOT EXISTS lehrgaenge (
            id INTEGER PRIMARY KEY,
            token TEXT UNIQUE,
            data TEXT,
            fetch_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    conn.commit()
    conn.close()

# Function to fetch and store data
def fetch_and_store_data():
    url = "https://alp.dillingen.de/-webservice-solr/alp-event/select?&fq=principal:false&q=*:*&sort=begin_date+asc&fq=is_cancelled:false&fq=(end_enrollment:[2100-12-31T00:00:00Z%20TO%20*]%20OR%20begin_date:[1900-01-01T00:00:00Z%20TO%20*])&rows=10000&start=0&wt=json&indent=on&facet=on&facet.limit=500&facet.field=schoolcategory&facet.field=keywords"
    response = requests.get(url)
    
    if response.status_code == 200:
        content = response.json()
        lehrgaenge = content['response']['docs']
        lehrgaenge_df = pd.DataFrame(lehrgaenge)
        
        conn = sqlite3.connect(DATABASE_PATH)
        for _, row in lehrgaenge_df.iterrows():
            try:
                conn.execute('INSERT INTO lehrgaenge (token, data) VALUES (?, ?)', (row['token'], json.dumps(row.to_dict())))
            except sqlite3.IntegrityError:
                # Ignore duplicate tokens
                pass
        conn.commit()
        conn.close()
    else:
        st.error("Failed to fetch data from the API")

# Function to load data from the database
@st.cache_data
def load_data():
    conn = sqlite3.connect(DATABASE_PATH)
    query = "SELECT * FROM lehrgaenge"
    df = pd.read_sql(query, conn)
    conn.close()
    df['fetch_date'] = pd.to_datetime(df['fetch_date'])
    
    # Convert the JSON strings in the 'data' column back to DataFrame
    df_data = pd.json_normalize(df['data'].apply(json.loads))
    df_data.columns = [f"json_{col}" for col in df_data.columns]  # Rename columns to avoid duplicates
    df = df.drop(columns=['data'])  # Drop the original 'data' column before merging
    df = pd.concat([df, df_data], axis=1)
    return df


# Initialize database
if not os.path.exists(DATABASE_PATH):
    initialize_database()

# Fetch and store data
fetch_and_store_data()

# Load data
df = load_data()