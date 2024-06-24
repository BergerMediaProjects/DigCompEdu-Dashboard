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

st.write("### DigCompEdu Bavaria Label Dashboard")

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
    url = "https://alp.dillingen.de/-webservice-solr/alp-event/select?&fq=principal:false&q=*:*&sort=begin_date+asc&fq=is_cancelled:false&fq=(end_enrollment:[2030-12-31T00:00:00Z%20TO%20*]%20OR%20begin_date:[2015-06-20T00:00:00Z%20TO%20*])&rows=20000&start=0&wt=json&indent=on&facet=on&facet.limit=500&facet.field=schoolcategory&facet.field=keywords"
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

# Save data frame to csv
df.to_csv('lehrgaenge_data.csv', index=False)

# Ensure 'token' is a string and categorize time periods
if 'json_token' in df.columns:
    df['json_token'] = df['json_token'].astype(str)
    
    # Match tokens with the format NNN/
    df['time_period'] = df['json_token'].apply(lambda x: x[:4] if re.match(r'\d{3}/', x[:4]) else 'other')
else:
    st.error("Token column is missing from the data")

# Mapping for the time periods
time_period_mapping = {
    "102/": "Aug '21 - Jan '22",
    "103/": "Feb '22 - Aug '22",
    "104/": "Aug '22 - Jan '23",
    "105/": "Feb '23 - Aug '23",
    "106/": "Sep '23 - Jan '24",
    "107/": "Feb '24 - Aug '24",
    "108/": "Sep '24 - Jan '25",
    "109/": "Feb '25 - Aug '25",
    "110/": "Sep '25 - Jan '26",
    "111/": "Feb '26 - Aug '26",
    "112/": "Sep '26 - Jan '27",
    "113/": "Feb '27 - Aug '27",
    "114/": "Sep '27 - Jan '28",
    "115/": "Feb '28 - Aug '28",
    "116/": "Sep '28 - Jan '29",
    "117/": "Feb '29 - Aug '29",
    "118/": "Sep '29 - Jan '30",
    "119/": "Feb '30 - Aug '30",
    "120/": "Sep '30 - Jan '31",
}

# Get unique time periods and append "Alle Zeiträume"
time_periods = df['time_period'].unique().tolist()
time_periods = [tp for tp in time_periods if tp in time_period_mapping]  # Filter only valid time periods
time_periods.append("Alle Zeiträume")

# Create a display mapping for dropdown
time_period_display = {tp: time_period_mapping.get(tp, tp) for tp in time_periods}
time_period_display["Alle Zeiträume"] = "Alle Zeiträume"

# Dropdown for time periods
selected_time_period_display = st.selectbox("Zeitraum wählen", list(time_period_display.values()))
selected_time_period = [k for k, v in time_period_display.items() if v == selected_time_period_display][0]

# Filter the DataFrame based on the selected schoolcategory and time periods
if selected_time_period != "Alle Zeiträume":
    filtered_df = df[df['time_period'] == selected_time_period]
else:
    filtered_df = df

# Check if 'json_schoolcategory' column exists
if 'json_schoolcategory' in df.columns:
    school_categories = df['json_schoolcategory'].explode().unique()
    school_categories = ["alle Schularten"] + list(school_categories)
else:
    school_categories = ["alle Schularten"]

selected_category = st.selectbox("Schulart wählen", school_categories)

if selected_category != "alle Schularten" and 'json_schoolcategory' in df.columns:
    filtered_df = filtered_df[filtered_df['json_schoolcategory'].apply(lambda x: selected_category in x if isinstance(x, list) else x == selected_category)]

# Count keywords in the filtered data
keyword_counts = count_keywords(filtered_df, keywords)

# Create a DataFrame for keyword counts
keyword_summary = pd.DataFrame(list(keyword_counts.items()), columns=['Keyword', 'Count'])

# Plot the keyword counts with custom colors
plt.figure(figsize=(10, 8))
ax = sns.barplot(data=keyword_summary, x='Count', y='Keyword', palette=[keywords_colors[keyword] for keyword in keyword_summary['Keyword']])
plt.title(f'Keyword Counts for {selected_category} ({selected_time_period_display})')
plt.xlabel('Count')
plt.ylabel('Keyword')
plt.xticks(size=8)
plt.yticks(size=8)

# Display plot in Streamlit app
st.pyplot(plt)

# Display the table with keyword counts below the plot
st.write("### DigCompEdu Bavaria Label - Häufigkeiten")
st.table(keyword_summary)
