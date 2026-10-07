import geopandas as gpd
from pathlib import Path
from typing import Optional
import zipfile
import tempfile
import os


class GeoProcessor:
    """Handle reading and processing geospatial files"""
    
    def read_file(self, file_path: Path, file_ext: str) -> gpd.GeoDataFrame:
        """
        Read a geospatial file and return a GeoDataFrame
        
        Args:
            file_path: Path to the file
            file_ext: File extension (.kml or .zip)
            
        Returns:
            GeoDataFrame with the features
        """
        try:
            if file_ext == '.kml':
                return self._read_kml(file_path)
            elif file_ext == '.zip':
                return self._read_shapefile_zip(file_path)
            else:
                raise ValueError(f"Unsupported file type: {file_ext}")
        except Exception as e:
            raise Exception(f"Error reading file: {str(e)}")
    
    def _read_kml(self, file_path: Path) -> gpd.GeoDataFrame:
        """Read a KML file"""
        try:
            # Use pyogrio to read KML (better compatibility)
            gdf = gpd.read_file(str(file_path), engine='pyogrio')
            
            # Validate that we got features
            if len(gdf) == 0:
                raise ValueError("KML file contains no features")
            
            return gdf
        except Exception as e:
            raise Exception(f"Failed to read KML file: {str(e)}")
    
    def _read_shapefile_zip(self, file_path: Path) -> gpd.GeoDataFrame:
        """Read a zipped Shapefile"""
        try:
            # Create a temporary directory to extract the zip
            with tempfile.TemporaryDirectory() as temp_dir:
                # Extract the zip file
                with zipfile.ZipFile(file_path, 'r') as zip_ref:
                    zip_ref.extractall(temp_dir)
                
                # Find the .shp file
                shp_files = list(Path(temp_dir).glob("*.shp"))
                
                if not shp_files:
                    raise ValueError("No .shp file found in the zip archive")
                
                if len(shp_files) > 1:
                    raise ValueError("Multiple .shp files found in the zip archive")
                
                shp_path = shp_files[0]
                
                # Read the shapefile
                gdf = gpd.read_file(str(shp_path))
                
                # Validate that we got features
                if len(gdf) == 0:
                    raise ValueError("Shapefile contains no features")
                
                return gdf
        except Exception as e:
            raise Exception(f"Failed to read Shapefile: {str(e)}")
