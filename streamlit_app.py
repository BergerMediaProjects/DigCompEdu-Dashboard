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
import subprocess

DATABASE_PATH = 'lehrgaenge_data.db'
FLAG_PATH = 'subprocess_ran.flag'

# Delete the flag file before running the subprocess
if os.path.exists(FLAG_PATH):
    os.remove(FLAG_PATH)

# Function to run the subprocess
def run_subprocess():
    # Delete the flag file before running the subprocess
    if os.path.exists(FLAG_PATH):
        os.remove(FLAG_PATH)
    
    init_file_path = os.path.join(os.path.dirname(__file__), 'init.py')
    result = subprocess.run(['.venv/bin/python3.11', init_file_path], capture_output=True, text=True)
    if result.returncode == 0:
        st.success("Datenbank erfolgreich geladen!")
        st.text(result.stdout)
        # Create a flag file to indicate the subprocess has run
        with open(FLAG_PATH, 'w') as flag_file:
            flag_file.write('subprocess has run')
    else:
        st.error("Fehler beim Initialisieren der Datenbank")
        st.text(result.stderr)
        st.stop()

# Check if the subprocess has run or if the database exists
if not os.path.exists(FLAG_PATH):
    st.info("Datenbank wird geladen.")
    run_subprocess()

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

# Load data
df = load_data()

st.write("### DigCompEdu Bavaria Label Dashboard")

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
time_periods.append("Alle verfügbaren Zeiträume")

# Create a display mapping for dropdown
time_period_display = {tp: time_period_mapping.get(tp, tp) for tp in time_periods}
time_period_display["Alle verfügbaren Zeiträume"] = "Alle verfügbaren Zeiträume"

# Dropdown for time periods
selected_time_period_display = st.selectbox("Zeitraum wählen", list(time_period_display.values()))
selected_time_period = [k for k, v in time_period_display.items() if v == selected_time_period_display][0]

# Filter the DataFrame based on the selected schoolcategory and time periods
if selected_time_period != "Alle verfügbaren Zeiträume":
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

# Selection of school subjects
school_subjects = ["alle Fächer", "Deutsch", "Englisch", "Mathematik", "Informatik", "Biologie", "Chemie", "Physik", "Musik", "Musikerziehung", "Kunst", "Französisch", "Latein", "Sport", "fächerübergreifend", "Fächerübergr. Bildungsaufgaben"]
selected_subject = st.selectbox("Schulfach wählen", school_subjects)

if selected_subject != "alle Fächer" and 'json_keywords' in df.columns:
    filtered_df = filtered_df[filtered_df['json_keywords'].apply(lambda x: selected_subject in x if isinstance(x, list) else x == selected_subject)]

# Check if 'json_eventtype' column exists
if 'json_eventtype' in df.columns:
    eventtype_categories = df['json_eventtype'].explode().unique()
    eventtype_categories = ["alle Formate"] + list(eventtype_categories)
else:
    eventtype_categories = ["alle Formate"]

selected_category = st.selectbox("Format wählen", eventtype_categories)

if selected_category != "alle Formate" and 'json_eventtype' in df.columns:
    filtered_df = filtered_df[filtered_df['json_eventtype'].apply(lambda x: selected_category in x if isinstance(x, list) else x == selected_category)]

# Selection of other keywords
other_keywords = ["kein Kriterium ausgewählt", "BayernCloud", "Unterricht_KI"]
other_keywords = st.selectbox("Weiteres Kriterium wählen", other_keywords)

if other_keywords != "kein Kriterium ausgewählt" and 'json_keywords' in df.columns:
    filtered_df = filtered_df[filtered_df['json_keywords'].apply(lambda x: other_keywords in x if isinstance(x, list) else x == other_keywords)]

# Count keywords in the filtered data
keyword_counts = count_keywords(filtered_df, keywords)

# Create a DataFrame for keyword counts
keyword_summary = pd.DataFrame(list(keyword_counts.items()), columns=['Keyword', 'Count'])

st.write("#### Barplot")

# Plot the keyword counts with custom colors
plt.figure(figsize=(10, 8))
ax = sns.barplot(data=keyword_summary, x='Count', y='Keyword', palette=[keywords_colors[keyword] for keyword in keyword_summary['Keyword']])
plt.title(f'Keyword Counts for {selected_category} ({selected_time_period_display})')
plt.xlabel('Count')
plt.ylabel('Keyword')
plt.xticks(size=8)
plt.yticks(size=8)

# Add labels inside the bars
for index, value in enumerate(keyword_summary['Count']):
    ax.text(value - 0.1, index, str(value), color='white', ha="right", va="center")

# Display plot in Streamlit app
st.pyplot(plt)

# Count the number of entries that are currently being plotted
num_entries_plotted = filtered_df.shape[0]

# Display the count in a Streamlit widget
st.write(f"Einträge gefunden: {num_entries_plotted}")

# Function to count entries in the database
def count_entries():
    conn = sqlite3.connect(DATABASE_PATH)
    query = "SELECT COUNT(*) FROM lehrgaenge"
    count = pd.read_sql(query, conn).iloc[0, 0]
    conn.close()
    return count

# Display the count in a Streamlit widget
entry_count = count_entries()
st.write(f"Einträge in der Datenbank: {entry_count}")

# Function to count keywords for each time period
def count_keywords_by_time_period(data, keywords, time_period_column='time_period'):
    keyword_counts = {keyword: [] for keyword in keywords}
    time_periods = data[time_period_column].unique()
    
    for time_period in sorted(time_periods):
        period_data = data[data[time_period_column] == time_period]
        period_counts = count_keywords(period_data, keywords)
        for keyword in keywords:
            keyword_counts[keyword].append(period_counts[keyword])
    
    return keyword_counts, sorted(time_periods)

# Calculate keyword counts for each time period
keyword_counts, time_periods = count_keywords_by_time_period(df, keywords)

# Convert keyword counts to a DataFrame for easier plotting
keyword_counts_df = pd.DataFrame(keyword_counts, index=time_periods)

# Map the time periods to their display labels
time_period_labels = [time_period_mapping.get(tp, tp) for tp in time_periods]

st.write(f"#### Zeitlicher Verlauf")

# Plot the evolution of keyword counts across time periods
plt.figure(figsize=(14, 8))
for keyword in keywords:
    plt.plot(time_period_labels, keyword_counts_df[keyword], label=keyword, color=keywords_colors[keyword])

plt.title('Keyword Counts Across Time Periods')
plt.xlabel('Time Period')
plt.ylabel('Count')
plt.legend(loc='upper left', bbox_to_anchor=(1, 1))
plt.xticks(rotation=45)
plt.tight_layout()

# Display the plot in the Streamlit app
st.pyplot(plt)

# Display the table with keyword counts below the plot
st.write("#### DigCompEdu Bavaria Label - Häufigkeiten")
st.table(keyword_summary)


