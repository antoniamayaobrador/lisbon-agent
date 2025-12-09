import geopandas as gpd
import pandas as pd
from shapely.geometry import Point

HOUSES_FILE = "data/synthetic_houses.geojson"
BOUNDARIES_FILE = "data/boundaries/lisboa_freguesias_oficial.geojson"

# Praça do Comércio coordinates (approximate)
PC_LAT, PC_LON = 38.7075, -9.1364

def run_analysis():
    print("Loading data...")
    houses = gpd.read_file(HOUSES_FILE)
    boundaries = gpd.read_file(BOUNDARIES_FILE)
    
    # Ensure CRS match (Project to UTM zone 29N - EPSG:32629 for accurate meters)
    # Or Web Mercator EPSG:3857 for simplicity
    target_crs = "EPSG:3857"
    houses_proj = houses.to_crs(target_crs)
    boundaries_proj = boundaries.to_crs(target_crs)
    
    print("-" * 30)
    print("Query 1: Which are the 5 most affordable freguesias?")
    
    # Spatial Join
    joined = gpd.sjoin(houses_proj, boundaries_proj, how="inner", predicate="within")
    
    # Identify the name column in boundaries (usually 'Freguesia' or 'Ni1')
    # Let's inspect columns if needed, but assuming 'Freguesia' based on typical data or check first column matching string
    name_col = None
    for col in ['Freguesia_x', 'Freguesia', 'NOME', 'name', 'Ni1']:
        if col in joined.columns:
            name_col = col
            break
            
    if name_col:
        # Calculate mean price per sqm by freguesia
        stats = joined.groupby(name_col)['price_sqm'].mean().sort_values()
        print(stats.head(5))
    else:
        print(f"Could not identify freguesia name column. Columns found: {joined.columns}")

    print("-" * 30)
    print("Query 2: Mean price of property 1500m around Praça do Comércio")
    
    # Create Point
    pc_point = gpd.GeoSeries([Point(PC_LON, PC_LAT)], crs="EPSG:4326").to_crs(target_crs)
    
    # Buffer 1500m
    buffer = pc_point.buffer(1500)
    
    # Filter houses within buffer
    # clip or intersects
    selection = houses_proj[houses_proj.geometry.within(buffer.iloc[0])]
    
    if not selection.empty:
        mean_price = selection['price'].mean()
        count = len(selection)
        print(f"Found {count} properties.")
        print(f"Mean Price: €{mean_price:,.2f}")
    else:
        print("No properties found within 1000m.")
        # Debug: find nearest
        distances = houses_proj.distance(pc_point.iloc[0])
        print(f"Nearest property is {distances.min():.2f} meters away.")

if __name__ == "__main__":
    run_analysis()
