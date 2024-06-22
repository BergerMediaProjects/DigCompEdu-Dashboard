import streamlit as st
import pandas as pd
import requests
import matplotlib.pyplot as plt
import seaborn as sns
import re

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
    
    # Debugging: Print the keyword columns and some of their content
    st.write("Keyword columns found:", keyword_columns)
    for col in keyword_columns:
        st.write(f"Sample data in column '{col}':", data[col].head())
    
    for keyword in keywords:
        regex_pattern = re.compile(r'\b' + re.escape(keyword) + r'\b', re.IGNORECASE)
        for column in keyword_columns:
            count = data[column].fillna("").apply(lambda x: bool(regex_pattern.search(str(x)))).sum()
            keyword_counts[keyword] += count
            # Debugging: Print keyword count
            st.write(f"Count for '{keyword}' in column '{column}': {count}")
    
    return keyword_counts

# Define the list of keywords and their associated colors
keywords_colors = {
    "Berufliche Kommunikation": "#c74300",
    "Kollegiale Zusammenarbeit": "#c74300",
    "Reflektiertes Handeln": "#c74300",
    "Digitale Weiterbildung": "#c74300",
    "Auswählen digitaler Ressourcen": "#00962c",
    "Erstellen und Anpassen digitaler Ressourcen": "#00962c",
    "Organisieren, Schützen und Teilen digitaler Ressourcen": "#00962c",
    "Lehren": "#245eb8",
    "Lernbegleitung": "#245eb8",
    "Kollaboratives Lernen": "#245eb8",
    "Selbstgesteuertes Lernen": "#245eb8",
    "Lernstand erheben": "#006a66",
    "Lern-Evidenzen analysieren": "#006a66",
    "Feedback und Planung": "#006a66",
    "Digitale Teilhabe": "#75006b",
    "Differenzierung und Individualisierung": "#75006b",
    "Aktive Einbindung der Lernenden": "#75006b",
    "Informations- und Medienkompetenz": "#8f0000",
    "Digitale Kommunikation und Zusammenarbeit": "#8f0000",
    "Erstellung digitaler Inhalte": "#8f0000",
    "Verantwortungsvoller Umgang mit digitalen Medien": "#8f0000",
    "Digitales Problemlösen": "#8f0000"
}

# Load data
df = load_data()

# Filter by schoolcategory
school_categories = df['schoolcategory'].explode().unique()
school_categories = ["alle Schularten"] + list(school_categories)
selected_category = st.selectbox("Select School Category", school_categories)

# Filter the DataFrame based on the selected schoolcategory
if selected_category != "alle Schularten":
    filtered_df = df[df['schoolcategory'].apply(lambda x: selected_category in x if isinstance(x, list) else x == selected_category)]
else:
    filtered_df = df

# Count keywords in the filtered data
keywords = list(keywords_colors.keys())
keyword_counts = count_keywords(filtered_df, keywords)

# Debugging: Check keyword counts
st.write("Keyword counts:", keyword_counts)

# Create a DataFrame for keyword counts
keyword_summary = pd.DataFrame(list(keyword_counts.items()), columns=['Keyword', 'Count'])

# Plot the keyword counts with custom colors
plt.figure(figsize=(10, 8))
ax = sns.barplot(data=keyword_summary, x='Count', y='Keyword', palette=[keywords_colors[keyword] for keyword in keyword_summary['Keyword']])
plt.title(f'Keyword Counts for {selected_category}')
plt.xlabel('Count')
plt.ylabel('Keyword')
plt.xticks(size=8)
plt.yticks(size=8)

# Display plot in Streamlit app
st.pyplot(plt)

# Display the table with keyword counts below the plot
st.write("### Keyword Counts Table")
st.table(keyword_summary)
