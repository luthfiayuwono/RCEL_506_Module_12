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
# ROW 2: Dropdown (Left) and Map (Right)
# ==========================================
col1, col2 = st.columns([1, 3])

# LEFT COLUMN: Dropdown Menu & Station Status
with col1:
    st.subheader("Search")
    
    id_to_name = dict(zip(df['station_id'], df['name']))
    station_list = df['station_id'].tolist()
    
    selected_station = st.selectbox(
        "Select a Station:", 
        options=station_list,
        format_func=lambda x: f"{x} - {id_to_name[x]}"
    )
    
    # --- NEW: DISPLAY STATION METRICS ---
    st.divider()
    st.subheader("📊 Station Status")
    
    # Grab the row of data specifically for the selected station
    station_data = df[df['station_id'] == str(selected_station)].iloc[0]
    
    # Display the metrics nicely
    # st.columns inside the left column to put metrics side-by-side!
    metric_col1, metric_col2 = st.columns(2)
    
    with metric_col1:
        st.metric(label="🚲 Bikes Available", value=station_data['num_bikes_available'])
        st.metric(label="🛠️ Disabled Bikes", value=station_data['num_bikes_disabled'])
        
    with metric_col2:
        st.metric(label="🅿️ Docks Available", value=station_data['num_docks_available'])
        st.metric(label="🚧 Disabled Docks", value=station_data['num_docks_disabled'])

# RIGHT COLUMN: The Map
with col2:
    # Initialize the map
    m = folium.Map(
        location=[df['lat'].mean(), df['lon'].mean()], 
        zoom_start=14
    )
def get_marker_color(bikes_available):
    if bikes_available == 0:
        return "red"
    elif bikes_available < 5:
        return "orange"
    else:
        return "green"
        
    # Add red markers ONLY for unselected stations
   for n in range(len(df)):
        if str(df['station_id'][n]) != str(selected_station):
            # Calculate color based on bikes
            marker_color = get_marker_color(df['num_bikes_available'][n])
            
            folium.Marker(
                location=[df['lat'][n], df['lon'][n]],
                tooltip=f"{df['station_id'][n]} - {df['name'][n]} (Bikes: {df['num_bikes_available'][n]})",
                icon=folium.Icon(color=marker_color, icon="bicycle", prefix='fa'),
            ).add_to(m)

    # Add the special cloud marker for the SELECTED station
    temp = df[df['station_id'] == str(selected_station)]
    
    if not temp.empty:
        folium.Marker(
            location=[temp.iloc[0]['lat'], temp.iloc[0]['lon']],
            tooltip=f"Selected: {temp.iloc[0]['station_id']} - {temp.iloc[0]['name']}",
            icon=folium.Icon(icon="cloud", color="blue"), 
        ).add_to(m)
    else:
        st.error('Station not found')

    # Render the Folium map
    st_folium(m, width=800, height=500)
