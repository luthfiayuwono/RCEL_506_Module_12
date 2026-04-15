import streamlit as st
import pandas as pd
import folium
from streamlit_folium import st_folium

# --- Setup Page Config ---
st.set_page_config(page_title="EcoBici Map", layout="wide")

# --- Dummy Data (Replace this with your actual DataFrame loading code) ---
# I'm adding this so the script runs perfectly out-of-the-box.
data = {
    'station_id': ['101', '102', '103', '104'],
    'lat': [19.4326, 19.4284, 19.4350, 19.4200],
    'lon': [-99.1332, -99.1415, -99.1400, -99.1500]
}
df = pd.DataFrame(data)


# ==========================================
# ROW 1: Title and Caption
# ==========================================
st.title("🚲 EcoBici Station Explorer")
st.caption("Created by: [Your Name Here]")

st.divider() # A nice visual line to separate the rows


# ==========================================
# ROW 2: Dropdown (Left) and Map (Right)
# ==========================================
# Create two columns. [1, 3] means the right column is 3 times wider than the left.
col1, col2 = st.columns([1, 3])

# LEFT COLUMN: Dropdown Menu
with col1:
    st.subheader("Search")
    # Streamlit's native dropdown widget replaces ipywidgets
    station_list = df['station_id'].tolist()
    
    # This automatically updates the variable when a user makes a selection
    selected_station = st.selectbox("Select a Station ID:", station_list)

# RIGHT COLUMN: The Map
with col2:
    # 1. Initialize the map
    m = folium.Map(
        location=[df['lat'].mean(), df['lon'].mean()], 
        zoom_start=14
    )

    # 2. Add red markers for ALL stations
    for n in range(len(df)):
        folium.Marker(
            location=[df['lat'][n], df['lon'][n]],
            tooltip=str(df['station_id'][n]),
            icon=folium.Icon(color="red"),
        ).add_to(m)

    # 3. Add the special cloud marker for the SELECTED station
    # We filter the dataframe based on the dropdown selection
    temp = df[df['station_id'] == str(selected_station)]
    
    if not temp.empty:
        # We use .iloc[0] to safely grab the exact float values for the map
        folium.Marker(
            location=[temp.iloc[0]['lat'], temp.iloc[0]['lon']],
            tooltip=f"Selected: {temp.iloc[0]['station_id']}",
            icon=folium.Icon(icon="cloud", color="blue"), # Made it blue so it stands out against the red!
        ).add_to(m)
    else:
        st.error('Station not found')

    # 4. Render the Folium map in Streamlit
    st_folium(m, width=800, height=500)
