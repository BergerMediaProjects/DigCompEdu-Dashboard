import streamlit as st
import pandas as pd
import requests
import matplotlib.pyplot as plt
import seaborn as sns
import re

# Display the heading and manual
st.title("DigCompEdu Bavaria-Analyse-Dashboard")
st.write("""
### Anleitung zur Verwendung des Dashboards

Verwenden Sie die Dropdown-Menüs unten, um die angezeigten Daten nach Schulart und Zeitraum zu filtern.

**Zeitraum auswählen:**
- **Feb. 2023 - Aug. 2023**: Daten von Februar 2023 bis August 2023
- **Sep. 2023 - Jan. 2024**: Daten von September 2023 bis Januar 2024
- **Feb. 2024 - Aug. 2024**: Daten von Februar 2024 bis August 2024
- **other**: Daten, die keinem der oben genannten Zeiträume entsprechen
- **Alle Zeiträume**: Alle verfügbaren Daten anzeigen

**Schulart auswählen:**
- Wählen Sie eine spezifische Schulart aus, um die Daten nur für diese Schulart anzuzeigen.
- Wählen Sie "alle Schularten", um die Daten für alle Schularten anzuzeigen.
""")

@st.cache_data
def load_data():
    url = "https://alp.dillingen.de/-webservice-solr/alp-event/select?&fq=principal:false&q=*:*&sort=begin_date+asc&fq=is_cancelled:false&fq=(end_enrollment:[2024-06-20T00:00:00Z%20TO%20*]%20OR%20begin_date:[2024-06-20T00:00:00Z%20TO%20*])&rows=10000&start=0&wt=json&indent=on&facet=on&facet.limit=500&facet.field=schoolcategory&facet.field=keywords"

    response = requests.get(url)
    if response.status_code == 200:
        content = response.json()
        lehrgaenge = content['response']['docs']
        lehrgaenge_list = [pd.DataFrame([item]) for item in lehrgaenge]
        lehrgaenge_df = pd.concat(lehrgaenge_list, ignore_index=True)
        
        if 'token' in lehrgaenge_df.columns:
            lehrgaenge_df['token_first_part'] = lehrgaenge_df['token'].str.split('_').str[0]
        
        return lehrgaenge_df
    else:
        st.error("Failed to fetch data from the API")
        return pd.DataFrame()

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

# Load data
df = load_data()

# Extract the first three characters from the token column to identify time periods
df['time_period'] = df['token'].str[:3]
time_periods = df['time_period'].unique().tolist()
time_periods.append("All Time Periods")

# Categorize any non-matching entries as "other"
df['time_period'] = df['time_period'].apply(lambda x: x if x in time_periods else "other")

# Filter by schoolcategory
school_categories = df['schoolcategory'].explode().unique()
school_categories = ["alle Schularten"] + list(school_categories)
selected_category = st.selectbox("Select School Category", school_categories)

# Filter by time periods
selected_time_period = st.selectbox("Select Time Period", time_periods)

# Filter the DataFrame based on the selected schoolcategory and time periods
if selected_time_period != "All Time Periods":
    filtered_df = df[df['time_period'] == selected_time_period]
else:
    filtered_df = df

if selected_category != "alle Schularten":
    filtered_df = filtered_df[filtered_df['schoolcategory'].apply(lambda x: selected_category in x if isinstance(x, list) else x == selected_category)]

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
