"""
Script to create sample KML and Shapefile files for testing
"""
import geopandas as gpd
from shapely.geometry import Polygon, LineString, Point
import zipfile
import os
import tempfile

# Create sample geometries
# Polygon (a simple rectangle in Chennai, India)
polygon_coords = [
    (80.2707, 13.0827),  # Chennai coordinates
    (80.2807, 13.0827),
    (80.2807, 13.0927),
    (80.2707, 13.0927),
    (80.2707, 13.0827)
]
polygon = Polygon(polygon_coords)

# LineString (a road segment)
line_coords = [
    (80.2707, 13.0827),
    (80.2757, 13.0877),
    (80.2807, 13.0927)
]
linestring = LineString(line_coords)

# Point (a location)
point = Point(80.2707, 13.0827)

# Create GeoDataFrame with WGS84 CRS (mixed geometries for KML)
gdf = gpd.GeoDataFrame(
    {
        'name': ['Sample Polygon', 'Sample Line', 'Sample Point'],
        'type': ['Park', 'Road', 'Landmark'],
        'desc': ['A park in Chennai', 'A road segment', 'A landmark location']
    },
    geometry=[polygon, linestring, point],
    crs="EPSG:4326"
)

# Save as KML
kml_path = "sample_chennai.kml"
gdf.to_file(kml_path, driver='KML')
print(f"Created KML file: {kml_path}")

# Create separate shapefiles for each geometry type (shapefiles only support one geometry type)
# Use a temporary directory to avoid permission issues
with tempfile.TemporaryDirectory() as temp_dir:
    # Polygon shapefile
    gdf_poly = gpd.GeoDataFrame(
        {
            'name': ['Sample Polygon'],
            'type': ['Park'],
            'desc': ['A park in Chennai']
        },
        geometry=[polygon],
        crs="EPSG:4326"
    )
    shp_poly_path = os.path.join(temp_dir, "sample_polygon")
    gdf_poly.to_file(shp_poly_path, driver='ESRI Shapefile')
    print(f"Created Polygon Shapefile in temp directory")

    # List all files created (recursively)
    print("Files in temp directory:")
    for root, dirs, files in os.walk(temp_dir):
        for f in files:
            print(f"  {os.path.join(root, f)}")

    # Zip the polygon shapefile (flatten the structure)
    zip_poly_path = "sample_polygon.zip"
    with zipfile.ZipFile(zip_poly_path, 'w') as zipf:
        files_added = False
        for root, dirs, files in os.walk(temp_dir):
            for f in files:
                file_path = os.path.join(root, f)
                # Use just the filename (flatten structure)
                arcname = os.path.basename(file_path)
                zipf.write(file_path, arcname)
                print(f"Added to zip: {arcname}")
                files_added = True
        
        if not files_added:
            print("Warning: No files found to zip")

    print(f"Created zipped Polygon Shapefile: {zip_poly_path}")

print("\nSample files created successfully!")
