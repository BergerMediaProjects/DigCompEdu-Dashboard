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
            keyword_counts[keyword] += data[column].fillna("").apply(lambda x: bool(regex_pattern.search(str(x)))).sum()
    
    return keyword_counts

# Define the list of keywords
keywords = [
    "Berufliche Kommunikation", "Kollegiale Zusammenarbeit", "Reflektiertes Handeln", "Kontinuierliche Weiterentwicklung",
    "Auswählen digitaler Ressourcen", "Erstellen und Anpassen digitaler Ressourcen", "Organisieren, Schützen und Teilen digitaler Ressourcen",
    "Lehren", "Lernbegleitung", "Kollaboratives Lernen", "Selbstgesteuertes Lernen",
    "Lernstandserhebung", "Analyse der Lernevidenz", "Feedback und 
