import streamlit as st
import pandas as pd
import folium
import requests  # <--- THIS WAS MISSING
from streamlit_folium import st_folium

# --- Setup Page Config ---
st.set_page_config(page_title="EcoBici Map", layout="wide")

# --- Fetch Data ---
url = 'https://gbfs.mex.lyftbikes.com/gbfs/gbfs.json'
website_data = requests.get(url).json()
urls = website_data['data']['en']['feeds']

# 1. Safely extract exact URLs based on the feed 'name' so they never get swapped
info_url = next(u['url'] for u in urls if u['name'] == 'station_information')
status_url = next(u['url'] for u in urls if u['name'] == 'station_status')

# 2. Load Station Information (Locations, Names)
data1 = requests.get(info_url).json()
df1 = pd.DataFrame(data1['data']['stations'])

# 3. Load Station Status (Available Bikes/Docks)
data2 = requests.get(status_url).json()
df2 = pd.DataFrame(data2['data']['stations'])

# 4. Safely select columns (Checking if 'capacity' exists first!)
info_columns = ['station_id', 'lat', 'lon']
if 'capacity' in df1.columns:
    info_columns.append('capacity')
df1 = df1[info_columns]

# 5. Select Status columns
df2 = df2[['station_id', 'num_bikes_available', 'num_bikes_disabled', 'num_docks_available', 'num_docks_disabled']]

# 6. Merge the two DataFrames
df = pd.merge(df1, df2, on='station_id')

# ==========================================
# ROW 1: Title and Caption
# ==========================================
st.title("🚲 EcoBici Station Explorer")
st.caption("Created by: Luthfia Yuwono")

st.divider() # A nice visual line to separate the rows

# ==========================================
# ROW 2: Dropdown (Left) and Map (Right)
# ==========================================
col1, col2 = st.columns([1, 3])

# LEFT COLUMN: Dropdown Menu
with col1:
    st.subheader("Search")
    station_list = df['station_id'].tolist()
    selected_station = st.selectbox("Select a Station ID:", station_list)

# RIGHT COLUMN: The Map
with col2:
    # 1. Initialize the map
    m = folium.Map(
        location=[df['lat'].mean(), df['lon'].mean()], 
        zoom_start=14
    )

    # 2. Add red markers ONLY for unselected stations
    for n in range(len(df)):
        if str(df['station_id'][n]) != str(selected_station):
            folium.Marker(
                location=[df['lat'][n], df['lon'][n]],
                tooltip=str(df['station_id'][n]),
                icon=folium.Icon(color="red"),
            ).add_to(m)

    # 3. Add the special cloud marker for the SELECTED station
    temp = df[df['station_id'] == str(selected_station)]
    
    if not temp.empty:
        folium.Marker(
            location=[temp.iloc[0]['lat'], temp.iloc[0]['lon']],
            tooltip=f"Selected: {temp.iloc[0]['station_id']}",
            icon=folium.Icon(icon="cloud", color="blue"), 
        ).add_to(m)
    else:
        st.error('Station not found')

    # 4. Render the Folium map in Streamlit (Removed the duplicate line)
    st_folium(m, width=800, height=500)
