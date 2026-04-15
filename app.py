import streamlit as st
import pandas as pd
import folium
import requests
from streamlit_folium import st_folium

# --- Setup Page Config ---
st.set_page_config(page_title="EcoBici Map", layout="wide")

# --- Fetch Data ---
url = 'https://gbfs.mex.lyftbikes.com/gbfs/gbfs.json'
website_data = requests.get(url).json()
urls = website_data['data']['en']['feeds']

info_url = next(u['url'] for u in urls if u['name'] == 'station_information')
status_url = next(u['url'] for u in urls if u['name'] == 'station_status')

data1 = requests.get(info_url).json()
df1 = pd.DataFrame(data1['data']['stations'])

data2 = requests.get(status_url).json()
df2 = pd.DataFrame(data2['data']['stations'])

info_columns = ['station_id', 'name', 'lat', 'lon']
if 'capacity' in df1.columns:
    info_columns.append('capacity')
df1 = df1[info_columns]

df2 = df2[['station_id', 'num_bikes_available', 'num_bikes_disabled', 'num_docks_available', 'num_docks_disabled']]
df = pd.merge(df1, df2, on='station_id')

# ==========================================
# ROW 1: Title and Caption
# ==========================================
st.title("🚲 EcoBici Station Explorer")
st.caption("Created by: Luthfia Yuwono")

st.divider()

# ==========================================
# ROW 2: Layout
# ==========================================
col1, col2 = st.columns([1, 3])

# LEFT COLUMN: Controls & Metrics
with col1:
    st.subheader("🎚️ Filter Map")
    max_bikes = int(df['num_bikes_available'].max())
    min_bikes = st.slider("Minimum bikes needed:", min_value=0, max_value=max_bikes, value=0)
    
    # Filter the dataframe and reset the index so our map loop doesn't break
    map_df = df[df['num_bikes_available'] >= min_bikes].reset_index(drop=True)
    
    st.divider()
    st.subheader("🔍 Search")
    
    # Only show dropdown and metrics if stations match the filter
    if not map_df.empty:
        id_to_name = dict(zip(map_df['station_id'], map_df['name']))
        station_list = map_df['station_id'].tolist()
        
        selected_station = st.selectbox(
            "Select a Station:", 
            options=station_list,
            format_func=lambda x: f"{x} - {id_to_name[x]}"
        )
        
        st.divider()
        st.subheader("📊 Station Status")
        
        station_data = map_df[map_df['station_id'] == str(selected_station)].iloc[0]
        
        metric_col1,
