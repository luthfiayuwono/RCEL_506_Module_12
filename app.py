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

# FIX: Force all station IDs to be strings (text) to prevent matching errors
df['station_id'] = df['station_id'].astype(str)

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
        
        # 1. INITIALIZE: Set default station if none exists
        if "station_selector" not in st.session_state:
            st.session_state["station_selector"] = station_list[0]
            
        # 2. MAP CLICK LOGIC: Check if the map was clicked BEFORE drawing the selectbox
        if "main_map" in st.session_state and st.session_state["main_map"].get("last_object_clicked_tooltip"):
            clicked_tooltip = st.session_state["main_map"]["last_object_clicked_tooltip"]
            
            # If they clicked an unselected station marker...
            if clicked_tooltip and not clicked_tooltip.startswith("Selected:"):
                # Extract the ID (e.g., "145 - Name" -> "145")
                clicked_id = clicked_tooltip.split(" - ")[0].strip()
                
                # If valid, immediately update the selectbox's memory
                if clicked_id in station_list:
                    st.session_state["station_selector"] = clicked_id

        # 3. SAFETY CHECK: If the selected station is filtered out by the slider, reset it
        if st.session_state["station_selector"] not in station_list:
            st.session_state["station_selector"] = station_list[0]
        
        # Draw the selectbox tied to our session state
        selected_station = st.selectbox(
            "Select a Station:", 
            options=station_list,
            format_func=lambda x: f"{x} - {id_to_name[x]}",
            key="station_selector"
        )
        
        st.divider()
        st.subheader("📊 Station Status")
        
        station_data = map_df[map_df['station_id'] == selected_station].iloc[0]
        
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
            st.write(f"**Station Capacity: {int(fill_percentage * 100)}% Full**")
            st.progress(float(fill_percentage))
            
        st.divider()
        google_maps_url = f"https://www.google.com/maps/dir/?api=1&destination={station_data['lat']},{station_data['lon']}"
        st.markdown(f"### [**🗺️ Get Directions to Station**]({google_maps_url})")
            
    else:
        st.warning("No stations match your filter. Please lower the slider.")
        selected_station = None

# RIGHT COLUMN: The Map
with col2:
    m = folium.Map(
        location=[df['lat'].mean(), df['lon'].mean()], 
        zoom_start=14
    )
    
    marker_cluster = MarkerCluster().add_to(m)

    def get_marker_color(amount):
        if amount == 0:
            return "red"
        elif amount < 5:
            return "orange"
        else:
            return "green"

    if not map_df.empty:
        for n in range(len(map_df)):
            if map_df.loc[n, 'station_id'] != selected_station:
                
                amount_here = map_df.loc[n, target_column]
                marker_color = get_marker_color(amount_here)
                map_icon = "bicycle" if user_mode == "🚲 Find a Bike" else "product-hunt"
                
                folium.Marker(
                    location=[map_df.loc[n, 'lat'], map_df.loc[n, 'lon']],
                    tooltip=f"{map_df.loc[n, 'station_id']} - {map_df.loc[n, 'name']} ({amount_here} available)",
                    icon=folium.Icon(color=marker_color, icon=map_icon, prefix='fa'),
                ).add_to(marker_cluster)

        # Draw the special cloud marker
        if selected_station:
            temp = map_df[map_df['station_id'] == selected_station]
            if not temp.empty:
                folium.Marker(
                    location=[temp.iloc[0]['lat'], temp.iloc[0]['lon']],
                    tooltip=f"Selected: {temp.iloc[0]['station_id']} - {temp.iloc[0]['name']}",
                    icon=folium.Icon(icon="cloud", color="blue"), 
                ).add_to(m)

    # Render the map and assign it a key so we can read its clicks globally!
    st_folium(m, width=800, height=500, key="main_map")
