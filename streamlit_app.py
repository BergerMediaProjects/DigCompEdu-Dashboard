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
import sys
import plotly

DATABASE_PATH = 'lehrgaenge_data.db'
FLAG_PATH = 'subprocess_ran.flag'

# Function to run the subprocess
def run_subprocess():
    st.write("Datenbank-Update läuft.")
    init_file_path = os.path.join(os.path.dirname(__file__), 'launch.py')
    result = subprocess.run([sys.executable, init_file_path], capture_output=True, text=True)
    if result.returncode == 0:
        st.success("Datenbank erfolgreich aktualisiert!")
        st.text(result.stdout)
        # Create a flag file to indicate the subprocess has run
        with open(FLAG_PATH, 'w') as flag_file:
            flag_file.write('subprocess has run')
    else:
        st.error("Fehler beim Initialisieren der Datenbank")
        st.text(result.stderr)
        st.stop()

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

# Ensure the subprocess runs only once during the initial page load
if 'subprocess_ran' not in st.session_state:
    st.session_state.subprocess_ran = False

if not st.session_state.subprocess_ran:
    st.session_state.subprocess_ran = True
    run_subprocess()

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

keywords = [
    "1.1 Berufliche Kommunikation",
    "1.2 Kollegiale Zusammenarbeit",
    "1.3 Reflektiertes Handeln",
    "1.4 Kontinuierliche Weiterentwicklung",
    "2.1 Auswählen digitaler Ressourcen",
    "2.2 Erstellen und Anpassen digitaler Ressourcen",
    "2.3 Organisieren, Schützen und Teilen digitaler Ressourcen",
    "3.1 Lehren",
    "3.2 Lernbegleitung",
    "3.3 Kollaboratives Lernen",
    "3.4 Selbstgesteuertes Lernen",
    "4.1 Lernstandserhebung",
    "4.2 Analyse der Lernevidenz",
    "4.3 Feedback und Planung",
    "5.1 Barrierefreiheit und digitale Teilhabe",
    "5.2 Differenzierung",
    "5.3 Schüleraktivierung",
    "6.1 Basiskompetenzen",
    "6.2 Suchen und Verarbeiten",
    "6.3 Kommunizieren und Kooperieren",
    "6.4 Produzieren und Präsentieren",
    "6.5 Analysieren und Reflektieren"
]

# Mapping updated keywords to their respective colors
keywords_colors = {
    "1.1 Berufliche Kommunikation": "#c74300",
    "1.2 Kollegiale Zusammenarbeit": "#c74300",
    "1.3 Reflektiertes Handeln": "#c74300",
    "1.4 Kontinuierliche Weiterentwicklung": "#c74300",
    "2.1 Auswählen digitaler Ressourcen": "#00962c",
    "2.2 Erstellen und Anpassen digitaler Ressourcen": "#00962c",
    "2.3 Organisieren, Schützen und Teilen digitaler Ressourcen": "#00962c",
    "3.1 Lehren": "#245eb8",
    "3.2 Lernbegleitung": "#245eb8",
    "3.3 Kollaboratives Lernen": "#245eb8",
    "3.4 Selbstgesteuertes Lernen": "#245eb8",
    "4.1 Lernstandserhebung": "#006a66",
    "4.2 Analyse der Lernevidenz": "#006a66",
    "4.3 Feedback und Planung": "#006a66",
    "5.1 Barrierefreiheit und digitale Teilhabe": "#75006b",
    "5.2 Differenzierung": "#75006b",
    "5.3 Schüleraktivierung": "#75006b",
    "6.1 Basiskompetenzen": "#8f0000",
    "6.2 Suchen und Verarbeiten": "#8f0000",
    "6.3 Kommunizieren und Kooperieren": "#8f0000",
    "6.4 Produzieren und Präsentieren": "#8f0000",
    "6.5 Analysieren und Reflektieren": "#8f0000"
}

# Ensure 'token' is a string and categorize time periods
if 'json_token' in df.columns:
    df['json_token'] = df['json_token'].astype(str)
    
    # Mapping for the time periods (bracketed codes omitted for display)
    time_period_mapping = {
        "102/": "Aug '21 - Jan '22",
        "103/": "Feb '22 - Aug '22",
        "104/": "Aug '22 - Jan '23",
        "105/": "Feb '23 - Aug '23",
        "106/": "Sep '23 - Jan '24",
        "23-24.1": "Sep '23 - Jan '24",
        "107/": "Feb '24 - Aug '24",
        "23-24.2": "Feb '24 - Aug '24",
        "108/": "Sep '24 - Jan '25",
        "24-25.1": "Sep '24 - Jan '25",
        "109/": "Feb '25 - Aug '25",
        "24-25.2": "Feb '25 - Aug '25",
        "110/": "Sep '25 - Jan '26",
        "25-26.1": "Sep '25 - Jan '26",
        "111/": "Feb '26 - Aug '26",
        "25-26.2": "Feb '26 - Aug '26",
        "112/": "Sep '26 - Jan '27",
        "26-27.1": "Sep '26 - Jan '27",
        "113/": "Feb '27 - Aug '27",
        "26-27.2": "Feb '27 - Aug '27",
        "114/": "Sep '27 - Jan '28",
        "27-28.1": "Sep '27 - Jan '28",
        "115/": "Feb '28 - Aug '28",
        "27-28.2": "Feb '28 - Aug '28",
        "116/": "Sep '28 - Jan '29",
        "28-29.1": "Sep '28 - Jan '29",
        "117/": "Feb '29 - Aug '29",
        "28-29.2": "Feb '29 - Aug '29",
        "118/": "Sep '29 - Jan '30",
        "29-30.1": "Sep '29 - Jan '30",
        "119/": "Feb '30 - Aug '30",
        "29-30.2": "Feb '30 - Aug '30",
        "120/": "Sep '30 - Jan '31",
        "30-31.1": "Sep '30 - Jan '31",
    }
    
    # Support both old (NNN/) and new (YY-YY.N) token formats
    def extract_time_period(token):
        if re.match(r'\d{3}/', token[:4]):
            return token[:4]
        match = re.match(r'(\d{2}-\d{2}\.\d)', token)
        if match:
            return match.group(1)
        return 'other'
    df['time_period'] = df['json_token'].apply(extract_time_period)
    # Filter out rows with 'other' as time_period (not mapped)
    df = df[df['time_period'].isin(list(time_period_mapping.keys()))]
else:
    st.error("Token column is missing from the data")



# Get unique time periods and append "Alle Zeiträume"

# Only use mapped time periods for dropdown and plots

# Build a mapping from display value to the first matching key in the mapping that is present in the data
display_to_key = {}
for tp in time_period_mapping.keys():
    if tp in df['time_period'].unique():
        display = time_period_mapping[tp]
        if display not in display_to_key:
            display_to_key[display] = tp
# Add the 'Alle verfügbaren Zeiträume' option
display_to_key["Alle verfügbaren Zeiträume"] = "Alle verfügbaren Zeiträume"

# Dropdown for time periods (deduplicated by display value)
selected_time_period_display = st.selectbox("Zeitraum wählen", list(display_to_key.keys()))
selected_time_period = display_to_key[selected_time_period_display]

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
    # Get unique time periods in the order of time_period_mapping
    period_order = [tp for tp in time_period_mapping.keys() if tp in data[time_period_column].unique()]
    for time_period in period_order:
        period_data = data[data[time_period_column] == time_period]
        period_counts = count_keywords(period_data, keywords)
        for keyword in keywords:
            keyword_counts[keyword].append(period_counts[keyword])
    return keyword_counts, period_order

# Calculate keyword counts for each time period
keyword_counts, time_periods = count_keywords_by_time_period(df, keywords)

# Convert keyword counts to a DataFrame for easier plotting

keyword_counts_df = pd.DataFrame(keyword_counts, index=time_periods)
# Map the time periods to their display labels, preserving order

time_period_labels = [time_period_mapping.get(tp, tp) for tp in time_periods]

# Prepare data for Plotly and aggregate duplicate periods, then sort by mapping order (needed for both Plotly and matplotlib)
keyword_counts_long = keyword_counts_df.reset_index().melt(id_vars='index', var_name='Keyword', value_name='Count')
keyword_counts_long = keyword_counts_long.rename(columns={'index': 'Time Period'})
keyword_counts_long['Time Period'] = keyword_counts_long['Time Period'].map(time_period_mapping).fillna(keyword_counts_long['Time Period'])
# Aggregate counts for each (Time Period, Keyword) pair
keyword_counts_long = keyword_counts_long.groupby(['Time Period', 'Keyword'], as_index=False)['Count'].sum()
# Sort by the order in time_period_mapping
period_order = list(dict.fromkeys(time_period_mapping.values()))
keyword_counts_long['Time Period'] = pd.Categorical(keyword_counts_long['Time Period'], categories=period_order, ordered=True)
keyword_counts_long = keyword_counts_long.sort_values(['Time Period', 'Keyword'])

st.write(f"#### Zeitlicher Verlauf")


# Plot the evolution of keyword counts across time periods using the aggregated data
plt.figure(figsize=(14, 8))
for keyword in keywords:
    data = keyword_counts_long[keyword_counts_long['Keyword'] == keyword]
    plt.plot(
        data['Time Period'],
        data['Count'],
        label=keyword,
        color=keywords_colors[keyword]
    )
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

import plotly.express as px

# Create a dictionary for custom colors based on the keywords
custom_colors = [keywords_colors[keyword] for keyword in keyword_summary['Keyword']]

# Create the Plotly bar plot
fig = px.bar(
    keyword_summary,
    x='Count',
    y='Keyword',
    orientation='h',
    color='Keyword',
    color_discrete_sequence=custom_colors,
    title=f'Keyword Counts for {selected_category} ({selected_time_period_display})'
)

# Update the layout for better readability
fig.update_layout(
    xaxis_title='Count',
    yaxis_title='Keyword',
    font=dict(size=12),
    title=dict(font=dict(size=18)),
    showlegend=False,
)

# Add labels inside the bars
for i in range(len(keyword_summary)):
    fig.add_annotation(
        x=keyword_summary['Count'][i],
        y=keyword_summary['Keyword'][i],
        text=str(keyword_summary['Count'][i]),
        showarrow=False,
        font=dict(color='white'),
        xanchor='right'
    )

#Headline for Plotly Plot
st.write("#### Interactive graphic")
# Display plot in Streamlit app
st.plotly_chart(fig)

import plotly.express as px

# Prepare data for Plotly and aggregate duplicate periods, then sort by mapping order
keyword_counts_long = keyword_counts_df.reset_index().melt(id_vars='index', var_name='Keyword', value_name='Count')
keyword_counts_long = keyword_counts_long.rename(columns={'index': 'Time Period'})
keyword_counts_long['Time Period'] = keyword_counts_long['Time Period'].map(time_period_mapping).fillna(keyword_counts_long['Time Period'])
# Aggregate counts for each (Time Period, Keyword) pair
keyword_counts_long = keyword_counts_long.groupby(['Time Period', 'Keyword'], as_index=False)['Count'].sum()
# Sort by the order in time_period_mapping
period_order = list(dict.fromkeys(time_period_mapping.values()))
keyword_counts_long['Time Period'] = pd.Categorical(keyword_counts_long['Time Period'], categories=period_order, ordered=True)
keyword_counts_long = keyword_counts_long.sort_values(['Time Period', 'Keyword'])

# Add a selectbox to choose a single keyword

selected_keyword = st.selectbox("Keyword für Verlauf wählen", keywords)
filtered_keyword_df = keyword_counts_long[keyword_counts_long['Keyword'] == selected_keyword]

# Create interactive line chart for the selected keyword

fig_single = px.line(
    filtered_keyword_df,
    x='Time Period',
    y='Count',
    markers=True,
    title=f"Verlauf für: {selected_keyword}",
    color_discrete_sequence=[keywords_colors[selected_keyword]]
)
fig_single.update_layout(
    xaxis_title='Time Period',
    yaxis_title='Count',
    font=dict(size=12),
    title=dict(font=dict(size=18)),
    hovermode='x unified',
    xaxis={'categoryorder':'array', 'categoryarray': period_order}
)
st.plotly_chart(fig_single, use_container_width=True)

# Create interactive line chart

fig = px.line(
    keyword_counts_long,
    x='Time Period',
    y='Count',
    color='Keyword',
    line_shape='linear',
    markers=True,
    color_discrete_map=keywords_colors,
    title='Keyword Counts Across Time Periods'
)
fig.update_layout(
    xaxis_title='Time Period',
    yaxis_title='Count',
    legend_title='Keyword',
    font=dict(size=12),
    title=dict(font=dict(size=18)),
    hovermode='x unified',
    xaxis={'categoryorder':'array', 'categoryarray': period_order}
)
st.plotly_chart(fig, use_container_width=True)