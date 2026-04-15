import streamlit as st
import pandas as pd
import folium
import requests
from streamlit_folium import st_folium
from folium.plugins import MarkerCluster

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
    user_mode = st.radio("What are you looking for?", ["🚲 Find a Bike", "🅿️ Find an Empty Dock"])
    
    if user_mode == "🚲 Find a Bike":
        target_column = 'num_bikes_available'
        slider_label = "Minimum bikes needed:"
    else:
        target_column = 'num_docks_available'
        slider_label = "Minimum empty docks needed:"

    st.subheader("🎚️ Filter Map")
    max_amount = int(df[target_column].max())
    min_amount = st.slider(slider_label, min_value=0, max_value=max_amount, value=0)
    
    map_df = df[df[target_column] >= min_amount].reset_index(drop=True)
    
    st.divider()
    st.subheader("🔍 Search")
    
    if not map_df.empty:
        id_to_name = dict(zip(map_df['station_id'], map_df['name']))
        station_list = map_df['station_id'].tolist()
        
        # NEW: Safety check. If the currently selected station gets filtered out by the slider, reset it.
        if "station_selector" in st.session_state and st.session_state["station_selector"] not in station_list:
            del st.session_state["station_selector"]
        
        # NEW: We added key="station_selector" to save this to Streamlit's session state
        selected_station = st.selectbox(
            "Select a Station:", 
            options=station_list,
            format_func=lambda x: f"{x} - {id_to_name[x]}",
            key="station_selector"
        )
        
        st.divider()
        st.subheader("📊 Station Status")
        
        station_data = map_df[map_df['station_id'] == str(selected_station)].iloc[0]
        
        metric_col1, metric_col2 = st.columns(2)
        
        with metric_col1:
            st.metric(label="🚲 Bikes Available", value=station_data['num_bikes_available'])
            st.metric(label="🛠️ Disabled Bikes", value=station_data['num_bikes_disabled'])
            
        with metric_col2:
            st.metric(label="🅿️ Docks Available", value=station_data['num_docks_available'])
            st.metric(label="🚧 Disabled Docks", value=station_data['num_docks_disabled'])
            
        total_slots = station_data['num_bikes_available'] + station_data['num_docks_available']
        if total_slots > 0:
            fill_percentage = station_data['num_bikes_available'] / total_slots
            st.write(f"**Station Capacity: {int(fill_percentage * 100
