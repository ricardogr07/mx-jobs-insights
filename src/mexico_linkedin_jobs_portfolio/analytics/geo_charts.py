"""Geographic visualizations using Folium for mapping job distribution by city."""

from __future__ import annotations

import base64
from io import BytesIO

from mexico_linkedin_jobs_portfolio.models import ReportMetrics

# Mexican city coordinates (latitude, longitude) for mapping
_CITY_COORDINATES = {
    "Mexico City": (19.4326, -99.1332),
    "Monterrey": (25.6866, -100.3161),
    "Guadalajara": (20.6596, -103.3496),
    "Cancún": (21.1629, -87.0739),
    "Playa del Carmen": (20.6379, -87.0739),
    "Querétaro": (20.5890, -100.4900),
    "Puebla": (19.0327, -98.2349),
    "León": (21.1344, -101.6821),
    "Tijuana": (32.5149, -117.0382),
    "Mérida": (20.9674, -89.6238),
    "Toluca": (19.2826, -99.6589),
    "Hermosillo": (29.0729, -110.9559),
    "Cuernavaca": (18.9186, -99.2381),
    "Chihuahua": (28.6353, -106.2688),
    "Culiacán": (24.8136, -107.3937),
    "Durango": (24.0277, -104.6532),
    "Saltillo": (25.4267, -101.0081),
    "San Luis Potosí": (22.1505, -100.9789),
    "Aguascalientes": (21.8853, -102.2917),
    "Torreón": (25.5428, -103.4181),
}


def map_to_base64_html(folium_map) -> str:
    """Convert Folium map object to base64-encoded HTML string for embedding.
    
    Args:
        folium_map: A folium.Map object
        
    Returns:
        Base64-encoded HTML string (data URI format)
    """
    try:
        html_output = folium_map._repr_html_()
        if isinstance(html_output, bytes):
            html_output = html_output.decode("utf-8")
        
        html_bytes = html_output.encode("utf-8")
        b64_string = base64.b64encode(html_bytes).decode("utf-8")
        return f"data:text/html;base64,{b64_string}"
    except Exception:
        return ""


def create_city_heatmap_layer(metrics: ReportMetrics, locale: str = "en") -> str:
    """Create interactive Folium map with heatmap layer showing job density by city.
    
    Features:
    - Heatmap layer with intensity based on job count
    - Circle markers with job count labels
    - Interactive pop-ups with city information
    - Mobile-responsive design
    
    Args:
        metrics: ReportMetrics object containing city_counts
        locale: Language for labels ("en" or "es")
    
    Returns:
        Base64-encoded HTML string (data URI) or empty string if folium unavailable
    """
    try:
        import folium
        from folium.plugins import HeatMap
    except ImportError:
        return ""
    
    # Mexico center coordinates
    mexico_center = [23.0, -102.0]
    
    # Create base map with light tileset
    map_obj = folium.Map(
        location=mexico_center,
        zoom_start=5,
        tiles="CartoDB positron",
        prefer_canvas=True,
        max_bounds=True,
    )
    
    # Prepare data for heatmap layer
    city_data = metrics.city_counts[:10]
    if not city_data:
        return ""
    
    max_count = max((c.count for c in city_data), default=1)
    
    # Heatmap expects [[lat, lon, intensity], ...]
    heatmap_data = []
    
    for city_info in city_data:
        if city_info.label in _CITY_COORDINATES:
            lat, lon = _CITY_COORDINATES[city_info.label]
            # Intensity: normalize to 0-1 range
            intensity = city_info.count / max_count
            heatmap_data.append([lat, lon, intensity])
    
    if heatmap_data:
        # Add heatmap layer
        HeatMap(
            heatmap_data,
            name="Job Density Heatmap" if locale == "en" else "Mapa de Densidad de Empleos",
            min_opacity=0.2,
            radius=40,
            blur=25,
            max_zoom=13,
            gradient={
                0.0: "#2166AC",  # Blue (cool)
                0.5: "#F7F7F7",  # White (neutral)
                1.0: "#B2182B",  # Red (hot)
            },
        ).add_to(map_obj)
    
    # Add circle markers with city names and job counts
    for city_info in city_data:
        if city_info.label in _CITY_COORDINATES:
            lat, lon = _CITY_COORDINATES[city_info.label]
            
            # Radius based on job count
            radius = 5 + (city_info.count / max_count) * 20
            
            # Popup text
            if locale == "es":
                popup_text = f"<b>{city_info.label}</b><br>Empleos: {city_info.count}"
                title_text = "Empleos"
            else:
                popup_text = f"<b>{city_info.label}</b><br>Jobs: {city_info.count}"
                title_text = "Jobs"
            
            folium.CircleMarker(
                location=[lat, lon],
                radius=radius,
                popup=folium.Popup(popup_text, max_width=200),
                tooltip=f"{city_info.label}: {city_info.count} {title_text}",
                color="#2166AC",
                fill=True,
                fillColor="#2166AC",
                fillOpacity=0.8,
                weight=2,
            ).add_to(map_obj)
    
    # Add title via custom HTML
    title_text = "Job Distribution Heatmap by City" if locale == "en" else "Mapa de Calor: Distribución de Empleos por Ciudad"
    title_html = f"""
    <div style="position: fixed; 
                top: 10px; left: 50px; width: 300px; height: auto;
                background-color: white; border: 2px solid grey; z-index: 9999;
                font-size: 14px; padding: 10px; border-radius: 5px;">
        <strong>{title_text}</strong>
    </div>
    """
    map_obj.get_root().html.add_child(folium.Element(title_html))
    
    # Add layer control
    folium.LayerControl().add_to(map_obj)
    
    return map_to_base64_html(map_obj)


def create_city_cluster_map(metrics: ReportMetrics, locale: str = "en") -> str:
    """Create interactive Folium map with MarkerCluster for city job distribution.
    
    Features:
    - Automatic cluster grouping at different zoom levels
    - Better performance with many markers
    - Color-coded intensity visualization
    
    Args:
        metrics: ReportMetrics object containing city_counts
        locale: Language for labels ("en" or "es")
    
    Returns:
        Base64-encoded HTML string (data URI) or empty string if folium unavailable
    """
    try:
        import folium
        from folium.plugins import MarkerCluster
    except ImportError:
        return ""
    
    # Mexico center coordinates
    mexico_center = [23.0, -102.0]
    
    # Create base map
    map_obj = folium.Map(
        location=mexico_center,
        zoom_start=5,
        tiles="CartoDB positron",
        prefer_canvas=True,
    )
    
    # Get city data
    city_data = metrics.city_counts[:10]
    if not city_data:
        return ""
    
    max_count = max((c.count for c in city_data), default=1)
    
    # Create marker cluster group
    marker_cluster = MarkerCluster(name="City Clusters" if locale == "en" else "Agrupaciones de Ciudades").add_to(map_obj)
    
    # Add markers to cluster
    for city_info in city_data:
        if city_info.label in _CITY_COORDINATES:
            lat, lon = _CITY_COORDINATES[city_info.label]
            
            # Color based on intensity
            intensity_ratio = city_info.count / max_count
            if intensity_ratio > 0.66:
                color = "red"
            elif intensity_ratio > 0.33:
                color = "orange"
            else:
                color = "blue"
            
            if locale == "es":
                popup_text = f"{city_info.label}<br>Empleos: {city_info.count}"
            else:
                popup_text = f"{city_info.label}<br>Jobs: {city_info.count}"
            
            folium.Marker(
                location=[lat, lon],
                popup=folium.Popup(popup_text, max_width=150),
                tooltip=city_info.label,
                icon=folium.Icon(color=color, icon="briefcase"),
            ).add_to(marker_cluster)
    
    # Add layer control
    folium.LayerControl().add_to(map_obj)
    
    return map_to_base64_html(map_obj)


def create_jobs_distribution_map_enhanced(metrics: ReportMetrics, locale: str = "en", heatmap: bool = True) -> str:
    """Create enhanced job distribution map with optional heatmap layer.
    
    This is the primary geographic visualization function that combines
    frequency heatmap with city markers for a comprehensive view.
    
    Args:
        metrics: ReportMetrics object containing city_counts
        locale: Language for labels ("en" or "es")
        heatmap: If True, use heatmap layer; if False, use cluster view
    
    Returns:
        Base64-encoded HTML string (data URI) or empty string if folium unavailable
    """
    if heatmap:
        return create_city_heatmap_layer(metrics, locale)
    else:
        return create_city_cluster_map(metrics, locale)
