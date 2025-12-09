import geopandas as gpd
import pandas as pd
import matplotlib.pyplot as plt
from langchain_core.tools import tool
from langchain_community.tools.tavily_search import TavilySearchResults
from typing import Optional
import os
import osmnx as ox
from shapely.geometry import Point

def _save_temp_gdf(gdf, name_prefix):
    """Helper to save a GeoDataFrame to a temp file and return path."""
    filename = f"data/{name_prefix}_result.geojson"
    # Ensure directory exists
    os.makedirs(os.path.dirname(filename), exist_ok=True)
    
    # Handle datetime columns for GeoJSON serialization
    for col in gdf.columns:
        if pd.api.types.is_datetime64_any_dtype(gdf[col]):
            gdf[col] = gdf[col].astype(str)
            
    gdf.to_file(filename, driver="GeoJSON")
    return filename

@tool
def load_geojson(file_path: str) -> str:
    """
    Loads a GeoJSON file and returns a summary of its contents (columns, standard deviation, etc).
    Use this to understand the data before joining or analyzing.
    """
    try:
        gdf = gpd.read_file(file_path)
        summary = f"Loaded {os.path.basename(file_path)}. Rows: {len(gdf)}. Columns: {list(gdf.columns)}\n"
        summary += f"CRS: {gdf.crs}\n"
        if 'geometry' in gdf.columns:
            summary += f"Geometry Type: {gdf.geometry.geom_type.unique()}\n"
        return summary
    except Exception as e:
        return f"Error loading file: {e}"

@tool
def spatial_join(left_file: str, right_file: str, how: str = "inner", predicate: str = "intersects") -> str:
    """
    Performs a spatial join between two GeoJSON files.
    'how': 'left', 'right', 'inner'
    'predicate': 'intersects', 'within', 'contains'
    Returns the path to the resulting GeoJSON file.
    """
    try:
        left_gdf = gpd.read_file(left_file)
        right_gdf = gpd.read_file(right_file)
        
        # Ensure CRS match
        if left_gdf.crs != right_gdf.crs:
            right_gdf = right_gdf.to_crs(left_gdf.crs)
            
        joined = gpd.sjoin(left_gdf, right_gdf, how=how, predicate=predicate)
        return _save_temp_gdf(joined, "spatial_join")
    except Exception as e:
        return f"Error executing spatial join: {e}"

@tool
def attribute_join(left_file: str, right_file: str, left_on: str, right_on: str, how: str = "inner") -> str:
    """
    Joins two datasets based on a common attribute (column).
    Returns path to result.
    """
    try:
        left_gdf = gpd.read_file(left_file)
        right_gdf = gpd.read_file(right_file)
        
        joined = left_gdf.merge(right_gdf, left_on=left_on, right_on=right_on, how=how)
        return _save_temp_gdf(joined, "attr_join")
    except Exception as e:
        return f"Error executing attribute join: {e}"

@tool
def analyze_data(file_path: str, python_code: str) -> str:
    """
    Executes Python code to analyze a GeoDataFrame loaded from `file_path`.
    The code must assume the dataframe is in a variable named `gdf`.
    The code must assign the final result (text or plot path) to a variable named `result`.
    
    Example code:
    "result = gdf['price'].mean()"
    "ax = gdf.plot(); plt.savefig('plot.png'); result = 'plot.png'"
    """
    try:
        gdf = gpd.read_file(file_path)
        
        # Safe globals for execution
        local_vars = {"gdf": gdf, "plt": plt, "pd": pd, "gpd": gpd, "result": None}
        
        # Create plots dir
        plot_dir = "data/plots"
        os.makedirs(plot_dir, exist_ok=True)
        import uuid
        plot_path = f"{plot_dir}/plot_{uuid.uuid4().hex[:8]}.png"
        local_vars["plot_path"] = plot_path
        
        exec(python_code, {}, local_vars)
        return str(local_vars.get("result", "No result variable set."))
    except Exception as e:
        return f"Error analyzing data: {e}"

@tool
def find_nearest(source_file: str, target_file: str, k: int = 1) -> str:
    """
    Finds the k nearest features in target_file for each feature in source_file.
    Returns path to result.
    """
    try:
        src = gpd.read_file(source_file)
        tgt = gpd.read_file(target_file)
        
        # Project to projected CRS for distance calculation (e.g., EPSG:3857 for meters)
        # Assuming input might be 4326. Smart projection or heuristic needed?
        # For Lisbon (Portugal), EPSG:3763 is good, or 3857 generic.
        if src.crs.is_geographic:
            src = src.to_crs(epsg=3857)
        if tgt.crs.is_geographic:
            tgt = tgt.to_crs(epsg=3857)
            
        # Use simple cKDTree or spatial join nearest
        # sjoin_nearest is available in modern geopandas
        joined = gpd.sjoin_nearest(src, tgt, how="left", distance_col="distance", max_distance=None)
        
        # Convert back to original CRS? Or keep projected. 
        # For usability, let's revert to 4326
        joined = joined.to_crs(epsg=4326)
        
        return _save_temp_gdf(joined, "nearest")
    except Exception as e:
        return f"Error finding nearest: {e}"

@tool
def get_street_network(place_name: str, network_type: str = "drive") -> str:
    """
    Fetches the street network for a given place name using OpenStreetMap.
    Network types: 'drive', 'walk', 'bike', 'all'.
    Returns the path to a GeoJSON file containing the network edges (streets).
    """
    try:
        # Fetch graph
        G = ox.graph_from_place(place_name, network_type=network_type)
        
        # Convert to GeoDataFrame
        gdf_nodes, gdf_edges = ox.graph_to_gdfs(G)
        
        # Reset index to ensure basic columns like 'u', 'v', 'key' are available
        gdf_edges = gdf_edges.reset_index()
        
        # Filter for useful columns to keep file size manageable and clean
        # Common OSM columns: 'osmid', 'name', 'highway', 'oneway', 'length', 'geometry'
        useful_cols = ['u', 'v', 'key', 'osmid', 'name', 'highway', 'oneway', 'length', 'geometry']
        available_cols = [c for c in useful_cols if c in gdf_edges.columns]
        gdf_edges = gdf_edges[available_cols]
        
        # Save to temp file
        output_path = _save_temp_gdf(gdf_edges, f"streets_{network_type}")
        
        summary = f"Fetched street network for '{place_name}' ({network_type}). Saved to {output_path}. Rows: {len(gdf_edges)}."
        return summary
    except Exception as e:
        return f"Error fetching street network: {e}"

@tool
def web_search(query: str) -> str:
    """
    Performs a web search using Tavily to find information, reviews, ratings, etc.
    Useful for questions about specific places, facilities, or current events.
    """
    try:
        # Tavily returns a list of results (dictionaries with 'url' and 'content')
        search = TavilySearchResults(max_results=3)
        results = search.invoke(query)
        
        # Format the results into a single string
        if isinstance(results, list):
            formatted = "\n".join([f"- {r.get('content')} (Source: {r.get('url')})" for r in results])
            return formatted
        return str(results)
    except Exception as e:
        return f"Error performing web search: {e}"
