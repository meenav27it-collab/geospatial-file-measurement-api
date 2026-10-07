import geopandas as gpd
from pyproj import CRS
from typing import Optional


class CRSHandler:
    """Handle Coordinate Reference System transformations"""
    
    def get_projected_crs(self, gdf: gpd.GeoDataFrame) -> str:
        """
        Determine the appropriate projected CRS for measurements
        
        For geographic CRS (like EPSG:4326), transform to a suitable projected CRS
        based on the geometry's location (UTM zone or local projection)
        
        Args:
            gdf: GeoDataFrame with geometries
            
        Returns:
            EPSG code of the projected CRS as string
        """
        if gdf.crs is None:
            # If no CRS, assume WGS84
            return "EPSG:4326"
        
        # Check if CRS is already projected
        if self._is_projected_crs(gdf.crs):
            return str(gdf.crs)
        
        # For geographic CRS, find appropriate UTM zone
        utm_crs = self._get_utm_zone(gdf)
        return utm_crs
    
    def _is_projected_crs(self, crs) -> bool:
        """Check if the CRS is projected (not geographic)"""
        try:
            crs_obj = CRS.from_user_input(crs)
            return crs_obj.is_projected
        except:
            return False
    
    def _get_utm_zone(self, gdf: gpd.GeoDataFrame) -> str:
        """
        Get the appropriate UTM zone for the geometries
        
        Args:
            gdf: GeoDataFrame with geometries
            
        Returns:
            EPSG code of the UTM zone as string
        """
        try:
            # Get the centroid of the first geometry to determine UTM zone
            geom = gdf.geometry.iloc[0]
            centroid = geom.centroid
            
            # Get coordinates
            lon = centroid.x
            lat = centroid.y
            
            # Calculate UTM zone
            utm_zone = int((lon + 180) / 6) + 1
            
            # Determine hemisphere (north or south)
            if lat >= 0:
                hemisphere = 'north'
                # EPSG codes for UTM North: 32601-32660
                epsg_code = 32600 + utm_zone
            else:
                hemisphere = 'south'
                # EPSG codes for UTM South: 32701-32760
                epsg_code = 32700 + utm_zone
            
            return f"EPSG:{epsg_code}"
        except Exception as e:
            # Fallback to Web Mercator if UTM calculation fails
            return "EPSG:3857"
