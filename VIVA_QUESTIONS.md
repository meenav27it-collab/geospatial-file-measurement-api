# 10 Likely Viva Questions and Answers

## 1. What is the purpose of this project and what problem does it solve?

**Answer:** This project is a Geospatial File Measurement API that allows users to upload KML and Shapefile geospatial data, extract features, and calculate accurate measurements (area for polygons, length for lines). The key problem it solves is handling Coordinate Reference System (CRS) transformations automatically - converting geographic coordinates (latitude/longitude in degrees) to projected coordinates (meters) to ensure accurate area and length calculations. Without this transformation, measurements calculated directly from degrees would be incorrect because degrees are angular units, not linear units.

## 2. Why do we need to transform coordinates from EPSG:4326 to a projected CRS like UTM?

**Answer:** EPSG:4326 (WGS84) is a geographic CRS that uses latitude and longitude in degrees. Calculating area or length directly from degrees gives incorrect results because:
- 1 degree of latitude ≈ 111 km (constant)
- 1 degree of longitude varies from 111 km at the equator to 0 km at the poles
- Degrees represent angles, not actual distances

Projected CRS like UTM uses meters as units, which are consistent across the map. By transforming to UTM, we ensure:
- Measurements are in real-world units (meters)
- Calculations are mathematically accurate
- Local measurements preserve precision

## 3. How does the UTM zone selection work in your implementation?

**Answer:** The UTM zone is calculated based on the centroid of the first geometry in the file:
1. Get the centroid coordinates (longitude, latitude)
2. Calculate UTM zone: `zone = int((longitude + 180) / 6) + 1`
3. Determine hemisphere based on latitude:
   - If latitude ≥ 0: UTM North (EPSG:326XX)
   - If latitude < 0: UTM South (EPSG:327XX)
4. Construct the EPSG code: 32600 + zone for North, 32700 + zone for South

For example, Chennai (80.27°E, 13.08°N) falls in UTM zone 44N, which is EPSG:32644.

## 4. What are the differences between KML and Shapefile formats?

**Answer:**
- **KML (Keyhole Markup Language)**:
  - XML-based text format
  - Can contain mixed geometry types (points, lines, polygons) in one file
  - Used by Google Earth
  - Human-readable
  - Contains style and attribute information

- **Shapefile**:
  - Binary format requiring multiple files (.shp, .shx, .dbf, .prj, .cpg)
  - Only supports one geometry type per file (all polygons or all lines)
  - Industry standard for GIS
  - Not human-readable
  - More efficient for large datasets

## 5. How do you handle different geometry types in the measurement logic?

**Answer:** The API checks the geometry type and applies appropriate measurements:
- **Polygon/MultiPolygon**: Calculate area using `.area` property → measurement_type = "area_sqm"
- **LineString/MultiLineString**: Calculate length using `.length` property → measurement_type = "length_m"
- **Point/MultiPoint**: No measurement (coordinates only) → measurement_type = "point" or "multipoint"
- **Unsupported geometries**: Gracefully handled with null measurement

The measurement is calculated after CRS transformation to ensure accuracy.

## 6. What libraries did you use and why?

**Answer:**
- **FastAPI**: Modern, fast web framework with automatic API documentation (Swagger/ReDoc)
- **GeoPandas**: Pandas extension for geospatial data, provides easy file reading and CRS handling
- **Shapely**: Geometry operations and calculations (area, length)
- **PyProj**: CRS transformations using PROJ library
- **Pydantic**: Data validation and serialization for API models
- **Uvicorn**: ASGI server to run FastAPI
- **React + Vite**: Modern frontend with fast build times
- **Axios**: HTTP client for API calls

## 7. How did you handle file uploads and security?

**Answer:**
- **File Validation**: Check file extension (.kml or .zip) before processing
- **Unique IDs**: Generate UUID for each uploaded file to prevent conflicts
- **Temporary Storage**: Files saved to uploads directory with unique names
- **In-Memory Storage**: GeoDataFrame stored in memory for demo (production would use database)
- **Error Handling**: Try-catch blocks with meaningful error messages
- **Future Security Improvements** (mentioned in README):
  - File size limits
  - Malware scanning
  - Authentication/authorization
  - Rate limiting

## 8. What is the difference between geographic and projected CRS?

**Answer:**
- **Geographic CRS**:
  - Uses angular units (degrees)
  - Coordinates are latitude/longitude
  - Represents positions on a 3D ellipsoid
  - Examples: EPSG:4326 (WGS84), EPSG:4269 (NAD83)
  - Not suitable for area/length calculations

- **Projected CRS**:
  - Uses linear units (meters, feet)
  - Coordinates are X/Y on a 2D plane
  - Created by projecting the ellipsoid onto a flat surface
  - Examples: UTM zones, Web Mercator (EPSG:3857)
  - Essential for accurate measurements

## 9. How does the API ensure data serialization and handle special values?

**Answer:** The API handles JSON serialization issues by:
- Converting pandas NaN values to None (null in JSON)
- Converting non-serializable types to strings
- Ensuring all property values are basic Python types (int, float, str, bool, None)
- Using Pydantic models for automatic validation and serialization
- This prevents errors when returning data with floating-point indices or special numeric values

## 10. What would you improve if this were a production application?

**Answer:**
- **Database Integration**: Replace in-memory storage with PostgreSQL + PostGIS or MongoDB
- **Cloud Storage**: Use S3 or Azure Blob for file storage instead of local disk
- **Authentication**: Add JWT-based authentication and user management
- **Async Processing**: Use Celery for background processing of large files
- **Caching**: Add Redis caching for frequently accessed files
- **File Cleanup**: Implement automatic cleanup of old uploads
- **Validation**: Add stricter file validation (size limits, content validation)
- **Logging**: Implement structured logging with log levels
- **Monitoring**: Add health checks, metrics, and alerting
- **Horizontal Scaling**: Deploy behind a load balancer with multiple instances
- **Rate Limiting**: Add rate limiting to prevent abuse
- **Additional Formats**: Support GeoJSON, GeoPackage, and other formats
