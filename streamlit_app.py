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
    
    for keyword in keywords:
        regex_pattern = re.compile(r'\b' + re.escape(keyword) + r'\b', re.IGNORECASE)
        for column in keyword_columns:
            keyword_counts[keyword] += data[column].fillna("").apply(lambda x: bool(regex_pattern.search(str(x)))).sum()
    
    return keyword_counts

# Define the list of keywords and their associated colors from the DigCompEdu Bavaria document
keywords_colors = {
    "Berufliche Kommunikation": "#1f77b4",  # Example color
    "Kollegiale Zusammenarbeit": "#ff7f0e",
    "Reflektiertes Handeln": "#2ca02c",
    "Kontinuierliche Weiterentwicklung": "#d62728",
    "Auswählen digitaler Ressourcen": "#9467bd",
    "Erstellen und Anpassen digitaler Ressourcen": "#8c564b",
    "Organisieren, Schützen und Teilen digitaler Ressourcen": "#e377c2",
    "Lehren": "#7f7f7f",
    "Lernbegleitung": "#bcbd22",
    "Kollaboratives Lernen": "#17becf",
    "Selbstgesteuertes Lernen": "#1f77b4",
    "Lernstandserhebung": "#ff7f0e",
    "Analyse der Lernevidenz": "#2ca02c",
    "Feedback und Planung": "#d62728",
    "Barrierefreiheit und digitale Teilhabe": "#9467bd",
    "Differenzierung": "#8c564b",
    "Schüleraktivierung": "#e377c2",
    "Basiskompetenzen": "#7f7f7f",
    "Suchen und Verarbeiten": "#bcbd22",
    "Kommunizieren und Kooperieren": "#17becf",
    "Produzieren und Präsentieren": "#1f77b4",
    "Analysieren und Reflektieren": "#ff7f0e"
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

# Create a DataFrame for keyword counts
keyword_summary = pd.DataFrame(list(keyword_counts.items()), columns=['Keyword', 'Count'])

# Plot the keyword counts with custom colors
plt.figure(figsize=(10, 8))
ax = sns.barplot(data=keyword_summary, x='Count', y='Keyword', palette=keywords_colors.values())
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
