import streamlit as st
import pandas as pd
import requests
import matplotlib.pyplot as plt
import seaborn as sns

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
        for column in keyword_columns:
            keyword_counts[keyword] += data[column].fillna("").str.contains(keyword, case=False, na=False).sum()
    
    return keyword_counts

# Define the list of keywords
keywords = [
    "Berufliche Kommunikation", "Kollegiale Zusammenarbeit", "Reflektiertes Handeln", "Kontinuierliche Weiterentwicklung",
    "Auswählen digitaler Ressourcen", "Erstellen und Anpassen digitaler Ressourcen", "Organisieren, Schützen und Teilen digitaler Ressourcen",
    "Lehren", "Lernbegleitung", "Kollaboratives Lernen", "Selbstgesteuertes Lernen",
    "Lernstandserhebung", "Analyse der Lernevidenz", "Feedback und Planung",
    "Barrierefreiheit und digitale Teilhabe", "Differenzierung", "Schüleraktivierung",
    "Basiskompetenzen", "Suchen und Verarbeiten", "Kommunizieren und Kooperieren",
    "Produzieren und Präsentieren", "Analysieren und Reflektieren"
]

# Load data
df = load_data()

# Debugging: Inspect the DataFrame structure
st.write("DataFrame structure:", df.head())

# Count keywords
keyword_counts = count_keywords(df, keywords)

# Create a DataFrame for keyword counts
keyword_summary = pd.DataFrame(list(keyword_counts.items()), columns=['Keyword', 'Count'])

# Reshape the data for visualization
# Assuming that you have school category counts separately as in your original code
# Dummy data for demonstration
gy_counts = [10, 15, 20]
gs_counts = [12, 18, 25]
ms_counts = [8, 14, 22]
rs_counts = [11, 19, 23]

# Example keywords list for matching counts (should be matched with actual keywords)
example_keywords = ["Keyword1", "Keyword2", "Keyword3"]

keyword_summary = pd.DataFrame({
    'Keyword': example_keywords,
    'Gymnasium': gy_counts,
    'Grundschule': gs_counts,
    'Mittelschule': ms_counts,
    'Realschule': rs_counts
})

# Reshape the data for visualization
keyword_summary_long = keyword_summary.melt(id_vars='Keyword', var_name='schoolcategory', value_name='Count')

# Plot the keyword counts for each school type
plt.figure(figsize=(10, 8))
sns.barplot(data=keyword_summary_long, x='Count', y='Keyword', hue='schoolcategory', dodge=True)
plt.title('Keyword Counts by School Type')
plt.xlabel('Count')
plt.ylabel('Keyword')
plt.legend(title='School Category')
plt.xticks(size=8)
plt.yticks(size=8)

# Display plot in Streamlit app
st.pyplot(plt)
