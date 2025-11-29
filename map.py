import folium
from folium import plugins

def create_map(latitude, longitude, zoom_start=12):
    """
    Create an interactive map with a custom marker at specified coordinates.
    
    Parameters:
    latitude (float): Latitude of the location
    longitude (float): Longitude of the location
    zoom_start (int): Initial zoom level of the map (default: 12)
    
    Returns:
    folium.Map: Interactive map object
    """
    # Create a map centered at the specified location
    m = folium.Map(location=[latitude, longitude], 
                   zoom_start=zoom_start,
                   tiles='OpenStreetMap')
    
    # Add a marker with a popup
    folium.Marker(
        [latitude, longitude],
        popup='Selected Location',
        icon=folium.Icon(color='red', icon='info-sign')
    ).add_to(m)
    
    # Add a circle around the marker
    folium.Circle(
        radius=1000,  # 1000 meters radius
        location=[latitude, longitude],
        color='crimson',
        fill=True,
    ).add_to(m)
    
    # Add fullscreen button
    plugins.Fullscreen().add_to(m)
    
    # Add location finder
    plugins.LocateControl().add_to(m)
    
    return m