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
    url = "https://alp.dillingen.de/-webservice-solr/alp-event/select?&fq=principal:false&q=*:*&sort=begin_date+asc&fq=is_cancelled:false&fq=(end_enrollment:[2024-06-20T00:00:00Z%20TO%20*]%20OR%20begin_date:[2024-06-20T00:00:00Z%20TO%20*])&rows=10000&start=0&wt=json&indent=on&facet=on&facet.limit=500&facet.field=schoolcategory&facet.field=keywords"
    response = requests.get(url)
    
    if response.status_code == 200:
        content = response.json()
        lehrgaenge = content['response']['docs']
        lehrgaenge_df = pd.DataFrame(lehrgaenge)
        
        # Log the columns for debugging
        st.write("Fetched data columns:", lehrgaenge_df.columns.tolist())
        
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

# Function to count keywords
def count_keywords(data, keywords):
    keyword_columns = [col for col in data.columns if 'keywords' in col.lower()]
    keyword_counts = {keyword: 0 for keyword in keywords}
    
    for keyword in keywords:
        regex_pattern = re.compile(r'\b' + re.escape(keyword) + r'\b', re.IGNORECASE)
        for column in keyword_columns:
            count = data[column].fillna("").apply(lambda x: bool(regex_pattern.search(str(x)))).sum()
            keyword_counts[keyword] += count
    
    return keyword_counts

# Initialize database
if not os.path.exists(DATABASE_PATH):
    initialize_database()

# Fetch and store data
fetch_and_store_data()

# Define the list of keywords and their associated colors
keywords = [
    "Berufliche Kommunikation", "Kollegiale Zusammenarbeit", "Reflektiertes Handeln", "Kontinuierliche Weiterentwicklung",
    "Auswählen digitaler Ressourcen", "Erstellen und Anpassen digitaler Ressourcen", "Organisieren, Schützen und Teilen digitaler Ressourcen",
    "Lehren", "Lernbegleitung", "Kollaboratives Lernen", "Selbstgesteuertes Lernen",
    "Lernstandserhebung", "Analyse der Lernevidenz", "Feedback und Planung",
    "Barrierefreiheit und digitale Teilhabe", "Differenzierung", "Schüleraktivierung",
    "Basiskompetenzen", "Suchen und Verarbeiten", "Kommunizieren und Kooperieren",
    "Produzieren und Präsentieren", "Analysieren und Reflektieren"
]

# Mapping keywords to their respective colors
keywords_colors = {
    "Berufliche Kommunikation": "#c74300",
    "Kollegiale Zusammenarbeit": "#c74300",
    "Reflektiertes Handeln": "#c74300",
    "Kontinuierliche Weiterentwicklung": "#c74300",
    "Auswählen digitaler Ressourcen": "#00962c",
    "Erstellen und Anpassen digitaler Ressourcen": "#00962c",
    "Organisieren, Schützen und Teilen digitaler Ressourcen": "#00962c",
    "Lehren": "#245eb8",
    "Lernbegleitung": "#245eb8",
    "Kollaboratives Lernen": "#245eb8",
    "Selbstgesteuertes Lernen": "#245eb8",
    "Lernstandserhebung": "#006a66",
    "Analyse der Lernevidenz": "#006a66",
    "Feedback und Planung": "#006a66",
    "Barrierefreiheit und digitale Teilhabe": "#75006b",
    "Differenzierung": "#75006b",
    "Schüleraktivierung": "#75006b",
    "Basiskompetenzen": "#8f0000",
    "Suchen und Verarbeiten": "#8f0000",
    "Kommunizieren und Kooperieren": "#8f0000",
    "Produzieren und Präsentieren": "#8f0000",
    "Analysieren und Reflektieren": "#8f0000"
}

# Load data
df = load_data()

# Debugging: print the first few rows to check the structure
st.write(df.head())

# Ensure 'token' is a string
if 'json_token' in df.columns:
    df['json_token'] = df['json_token'].astype(str)
    df['time_period'] = df['json_token'].str[:3]
else:
    st.error("Token column is missing from the data")

time_periods = df['time_period'].unique().tolist()
time_periods.append("All Time Periods")

# Categorize any non-matching entries as "other"
df['time_period'] = df['time_period'].apply(lambda x: x if x in time_periods else "other")

# Check if 'json_schoolcategory' column exists
if 'json_schoolcategory' in df.columns:
    school_categories = df['json_schoolcategory'].explode().unique()
    school_categories = ["alle Schularten"] + list(school_categories)
else:
    school_categories = ["alle Schularten"]

selected_category = st.selectbox("Select School Category", school_categories)

# Filter by time periods
selected_time_period = st.selectbox("Select Time Period", time_periods)

# Filter the DataFrame based on the selected schoolcategory and time periods
if selected_time_period != "All Time Periods":
    filtered_df = df[df['time_period'] == selected_time_period]
else:
    filtered_df = df

if selected_category != "alle Schularten" and 'json_schoolcategory' in df.columns:
    filtered_df = filtered_df[filtered_df['json_schoolcategory'].apply(lambda x: selected_category in x if isinstance(x, list) else x == selected_category)]

# Count keywords in the filtered data
keyword_counts = count_keywords(filtered_df, keywords)

# Create a DataFrame for keyword counts
keyword_summary = pd.DataFrame(list(keyword_counts.items()), columns=['Keyword', 'Count'])

# Plot the keyword counts with custom colors
plt.figure(figsize=(10, 8))
ax = sns.barplot(data=keyword_summary, x='Count', y='Keyword', palette=[keywords_colors[keyword] for keyword in keyword_summary['Keyword']])
plt.title(f'Keyword Counts for {selected_category} ({selected_time_period})')
plt.xlabel('Count')
plt.ylabel('Keyword')
plt.xticks(size=8)
plt.yticks(size=8)

# Display plot in Streamlit app
st.pyplot(plt)

# Display the table with keyword counts below the plot
st.write("### Keyword Counts Table")
st.table(keyword_summary)
