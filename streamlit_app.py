import altair as alt
import pandas as pd
import streamlit as st

# Show the page title and description.
st.set_page_config(page_title="ALP Dillingen", page_icon="🎬")
st.title("DigCompEdu Bavaria")
st.write(
    """
    This app visualizes data from [ALP Dillingen](https://alp.dillingen.de/lehrerfortbildung/lehrgangsangebote/lehrgangssuche/).

    """
)

import streamlit as st
import pandas as pd
import requests

# Load the data from the API. We're caching this so it doesn't reload every time the app
# reruns (e.g. if the user interacts with the widgets).
@st.cache_data
def load_data():
    url = "https://alp.dillingen.de/-webservice-solr/alp-event/select?&fq=principal:false&q=*:*&sort=begin_date+asc&fq=is_cancelled:false&fq=(end_enrollment:[2024-06-20T00:00:00Z%20TO%20*]%20OR%20begin_date:[2024-06-20T00:00:00Z%20TO%20*])&rows=10000&start=0&wt=json&indent=on&facet=on&facet.limit=500&facet.field=schoolcategory&facet.field=keywords"

    response = requests.get(url)
    if response.status_code == 200:
        content = response.json()
        # Extract the relevant data from the JSON response
        lehrgaenge = content['response']['docs']
        
        # Convert each entry to a data frame and then concatenate them together
        lehrgaenge_list = [pd.DataFrame([item]) for item in lehrgaenge]
        lehrgaenge_df = pd.concat(lehrgaenge_list, ignore_index=True)
        
        # Add a new column containing the first part of the "token" variable
        if 'token' in lehrgaenge_df.columns:
            lehrgaenge_df['token_first_part'] = lehrgaenge_df['token'].str.split('/').str[0] # Assuming the delimiter is an underscore
        
        
        return lehrgaenge_df
    else:
        st.error("Failed to fetch data from the API")
        return pd.DataFrame()

# Load data
df = load_data()

# Display data in Streamlit app
st.write(df)



# Show a multiselect widget with the school types using `st.multiselect`.
schooltype = st.multiselect(
    "Schulart",
    df.schooltype.unique(),
    ["Grundschule", "Realschule", "Gymnasium", "Mittelschule"],
)


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

# Load data
df = load_data()

# Assuming gy_counts, gs_counts, ms_counts, rs_counts, and keywords are columns in the DataFrame
# Combine the counts into a single data frame for summary
keyword_summary = pd.DataFrame({
    'Keyword': df['keywords'],
    'Gymnasium': df['gy_counts'],
    'Grundschule': df['gs_counts'],
    'Mittelschule': df['ms_counts'],
    'Realschule': df['rs_counts']
})

# Reshape the data for visualization
keyword_summary_long = keyword_summary.melt(id_vars='Keyword', var_name='SchoolType', value_name='Count')

# Plot the keyword counts for each school type
plt.figure(figsize=(10, 8))
sns.barplot(data=keyword_summary_long, x='Count', y='Keyword', hue='SchoolType', dodge=True)
plt.title('Keyword Counts by School Type')
plt.xlabel('Count')
plt.ylabel('Keyword')
plt.legend(title='SchoolType')
plt.xticks(size=8)
plt.yticks(size=8)
plt.show()

# Display plot in Streamlit app
st.pyplot(plt)



# Show a slider widget with the years using `st.slider`.
years = st.slider("Years", 1986, 2006, (2000, 2016))

# Filter the dataframe based on the widget input and reshape it.
df_filtered = df[(df["genre"].isin(genres)) & (df["year"].between(years[0], years[1]))]
df_reshaped = df_filtered.pivot_table(
    index="year", columns="genre", values="gross", aggfunc="sum", fill_value=0
)
df_reshaped = df_reshaped.sort_values(by="year", ascending=False)


# Display the data as a table using `st.dataframe`.
st.dataframe(
    df_reshaped,
    use_container_width=True,
    column_config={"year": st.column_config.TextColumn("Year")},
)

# Display the data as an Altair chart using `st.altair_chart`.
df_chart = pd.melt(
    df_reshaped.reset_index(), id_vars="year", var_name="genre", value_name="gross"
)
chart = (
    alt.Chart(df_chart)
    .mark_line()
    .encode(
        x=alt.X("year:N", title="Year"),
        y=alt.Y("gross:Q", title="Gross earnings ($)"),
        color="genre:N",
    )
    .properties(height=320)
)
st.altair_chart(chart, use_container_width=True)
