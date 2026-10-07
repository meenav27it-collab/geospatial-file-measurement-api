# Geospatial File Measurement API

A complete, production-ready API for uploading and measuring geospatial files (KML and Shapefiles) with automatic CRS transformation and accurate area/length calculations.

## Features

- **File Upload**: Support for KML files and zipped Shapefiles
- **Feature Extraction**: Extract geometry type, coordinates, CRS, and attributes for every feature
- **Accurate Measurements**: Calculate polygon areas (m²) and line lengths (m) with proper CRS handling
- **Automatic CRS Transformation**: Converts geographic coordinates (EPSG:4326) to appropriate projected CRS (UTM) for accurate measurements
- **Web Dashboard**: Professional drag-and-drop interface for file upload and visualization
- **API Documentation**: Interactive Swagger UI and ReDoc
- **Comprehensive Testing**: Pytest test suite

## Tech Stack

### Backend
- **FastAPI**: Modern, fast web framework for building APIs
- **GeoPandas**: Python tools for geospatial data
- **Shapely**: Manipulation and analysis of geometric objects
- **PyProj**: Python interface to PROJ coordinate transformation library
- **Pydantic**: Data validation using Python type annotations
- **Uvicorn**: ASGI server

### Frontend
- **React**: UI library
- **Vite**: Build tool and dev server
- **Axios**: HTTP client

## Architecture

```
geospatial-api/
├── backend/
│   ├── app/
│   │   ├── main.py              # FastAPI application and endpoints
│   │   ├── models.py            # Pydantic models for request/response
│   │   ├── geo_processor.py     # File reading and processing logic
│   │   └── crs_handler.py       # CRS transformation logic
│   ├── tests/
│   │   └── test_api.py          # API tests
│   ├── sample_files/
│   │   ├── sample_chennai.kml   # Sample KML file
│   │   ├── sample_polygon.zip   # Sample zipped Shapefile
│   │   └── create_sample_files.py # Script to generate samples
│   ├── uploads/                 # Temporary file storage
│   ├── requirements.txt         # Python dependencies
│   └── venv/                    # Virtual environment
└── frontend/
    ├── src/
    │   ├── App.jsx             # Main React component
    │   ├── App.css             # Styling
    │   └── main.jsx            # Entry point
    ├── dist/                   # Built frontend
    └── package.json           # Node dependencies
```

## File Processing Flow

1. **Upload**: User uploads a KML or zipped Shapefile via the API
2. **Validation**: File extension is validated (.kml or .zip)
3. **Storage**: File is saved to the uploads directory with a unique ID
4. **Reading**:
   - KML: Read using GeoPandas with Fiona engine
   - Shapefile: Extract zip, find .shp file, read with GeoPandas
5. **Extraction**: For each feature, extract:
   - Feature ID/index
   - Geometry type (Point, LineString, Polygon, etc.)
   - Geometry coordinates
   - Source CRS
   - Properties/attributes
6. **Storage**: File info and GeoDataFrame stored in memory (for demo purposes)

## Measurement Logic

### CRS Strategy

The API implements a robust CRS handling strategy:

1. **Check Source CRS**: Determine if the file has a CRS defined
2. **Geographic vs Projected**:
   - If CRS is already projected (units in meters), use it directly
   - If CRS is geographic (degrees, e.g., EPSG:4326), transform to projected
3. **UTM Zone Selection**:
   - Calculate centroid of the first geometry
   - Determine appropriate UTM zone based on longitude
   - Select UTM North (EPSG:326XX) or South (EPSG:327XX) based on latitude
   - Fallback to Web Mercator (EPSG:3857) if UTM calculation fails

### Measurement Calculations

- **Polygon/MultiPolygon**: Area in square meters using `.area` property
- **LineString/MultiLineString**: Length in meters using `.length` property
- **Point/MultiPoint**: No measurement (coordinates only)
- **Unsupported Geometries**: Gracefully handled with null measurement

### Why CRS Transformation Matters

Directly calculating area/length from latitude/longitude degrees gives incorrect results because:
- 1 degree of latitude ≈ 111 km
- 1 degree of longitude varies from 111 km (equator) to 0 km (poles)
- Degrees are angular units, not linear units

By transforming to a projected CRS (like UTM), we ensure:
- Measurements are in real-world units (meters)
- Accuracy is preserved for local measurements
- Calculations are mathematically correct

## Design Decisions

### In-Memory Storage
For this demo, file data is stored in memory using a Python dictionary. In production, you would:
- Use a database (PostgreSQL with PostGIS, MongoDB, etc.)
- Store files in cloud storage (S3, Azure Blob, etc.)
- Implement proper cleanup for temporary files

### UTM Zone Calculation
UTM zones are calculated based on the centroid of the first feature. This is a simplification; for large datasets spanning multiple zones, you might:
- Calculate the most common UTM zone
- Use a local projected CRS
- Split features by zone

### Shapefile Limitations
Shapefiles only support one geometry type per file. The sample Shapefile contains only polygons. KML files can contain mixed geometry types.

### Error Handling
- File type validation before processing
- Graceful handling of unsupported geometries
- Clear error messages returned to the client
- Fallback to Web Mercator if UTM calculation fails

## Setup Instructions

### Prerequisites
- Python 3.11 or higher
- Node.js 18 or higher
- Git

### Windows Setup

#### 1. Clone the Repository
```bash
git clone <repository-url>
cd geospatial-api
```

#### 2. Backend Setup

```bash
cd backend

# Create virtual environment
python -m venv venv

# Activate virtual environment
venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

#### 3. Frontend Setup

```bash
cd frontend

# Install dependencies
npm install

# Build for production
npm run build
```

#### 4. Run the Application

```bash
# From the backend directory
cd backend
venv\Scripts\activate

# Run the FastAPI server
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

The application will be available at:
- Frontend: http://localhost:8000
- API: http://localhost:8000/api/
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

## API Documentation

### Endpoints

#### Health Check
```
GET /health
```
Returns the health status of the API.

**Response:**
```json
{
  "status": "healthy",
  "service": "Geospatial File Measurement API"
}
```

#### Upload File
```
POST /api/files/
Content-Type: multipart/form-data
```

Upload a KML or zipped Shapefile.

**Request:**
- `file`: The file to upload (required)

**Response:**
```json
{
  "id": "uuid",
  "filename": "sample.kml",
  "file_type": "kml",
  "status": "processed",
  "feature_count": 3,
  "crs": "EPSG:4326"
}
```

#### Get File Details
```
GET /api/files/{id}/
```

Get details of an uploaded file including all features.

**Response:**
```json
{
  "id": "uuid",
  "filename": "sample.kml",
  "file_type": "kml",
  "crs": "EPSG:4326",
  "feature_count": 3,
  "features": [
    {
      "id": 0,
      "geometry_type": "Polygon",
      "geometry": "POLYGON ((80.2707 13.0827, ...))",
      "properties": {
        "name": "Sample Polygon",
        "type": "Park"
      }
    }
  ]
}
```

#### Get Measurements
```
GET /api/files/{id}/measurements/
```

Get measurements for all features in a file.

**Response:**
```json
{
  "file_id": "uuid",
  "source_crs": "EPSG:4326",
  "measurement_crs": "EPSG:32644",
  "measurements": [
    {
      "feature_id": 0,
      "geometry_type": "Polygon",
      "measurement": 1234567.89,
      "measurement_type": "area_sqm",
      "properties": {
        "name": "Sample Polygon",
        "type": "Park"
      }
    }
  ]
}
```

## Testing

### Run Tests

```bash
cd backend
venv\Scripts\activate
pytest tests/ -v
```

### Test Coverage

The test suite includes:
- Health check endpoint
- KML file upload
- Shapefile upload
- Invalid file type handling
- File details retrieval
- Measurement retrieval
- CRS transformation verification
- Polygon area calculation
- Point measurement handling

## Docker Instructions

### Build the Docker Image

```bash
cd backend
docker build -t geospatial-api .
```

### Run with Docker

```bash
docker run -p 8000:8000 geospatial-api
```

### Docker Compose (Optional)

Create a `docker-compose.yml` file:

```yaml
version: '3.8'
services:
  api:
    build: ./backend
    ports:
      - "8000:8000"
    volumes:
      - ./backend/uploads:/app/uploads
```

Run with:
```bash
docker-compose up
```

## GitHub Instructions

### Initial Setup

```bash
# Initialize git repository
git init

# Add all files
git add .

# Commit
git commit -m "Initial commit: Geospatial File Measurement API"

# Add remote
git remote add origin <your-github-repo-url>

# Push
git push -u origin main
```

### .gitignore

A `.gitignore` file is included to exclude:
- Virtual environments
- Node modules
- Uploads directory
- Python cache files
- OS-specific files

## Deployment Instructions

### Production Deployment Checklist

1. **Environment Variables**:
   - Set `UPLOAD_DIR` to a persistent storage location
   - Configure CORS for your domain
   - Set appropriate security headers

2. **Database**:
   - Replace in-memory storage with a database
   - Use PostGIS for spatial data if using PostgreSQL

3. **File Storage**:
   - Use cloud storage (S3, Azure Blob) for uploaded files
   - Implement proper cleanup policies

4. **Security**:
   - Add authentication/authorization
   - Implement rate limiting
   - Validate file size limits
   - Scan uploaded files for malware

5. **Monitoring**:
   - Add logging
   - Set up health checks
   - Monitor performance metrics

### Deployment Platforms

#### Railway
```bash
railway login
railway init
railway up
```

#### Render
```bash
# Deploy backend
cd backend
railway deploy

# Deploy frontend
cd frontend
railway deploy
```

#### AWS/Azure/GCP
- Use their respective CLI tools or web consoles
- Deploy backend as a container or serverless function
- Deploy frontend to static hosting (S3, CloudFront, etc.)

## Learning Section

### Key Concepts

#### Coordinate Reference Systems (CRS)
- **Geographic CRS**: Uses latitude/longitude (degrees), e.g., EPSG:4326 (WGS84)
- **Projected CRS**: Uses linear units (meters, feet), e.g., UTM zones, Web Mercator
- **Why it matters**: Area/length calculations require projected CRS for accuracy

#### Geospatial File Formats
- **KML**: XML-based format, supports mixed geometry types, used by Google Earth
- **Shapefile**: Binary format, requires multiple files (.shp, .shx, .dbf, .prj), only one geometry type per file

#### Geometry Types
- **Point**: Single location (x, y)
- **LineString**: Sequence of points forming a line
- **Polygon**: Closed shape with area
- **Multi* versions**: Collections of the above

#### UTM Zones
- World divided into 60 zones, each 6° of longitude wide
- Zones numbered 1-60, starting from -180°
- Each zone has a North (EPSG:326XX) and South (EPSG:327XX) projection
- Provides accurate local measurements

### Resources
- [GeoPandas Documentation](https://geopandas.org/)
- [Shapely Documentation](https://shapely.readthedocs.io/)
- [PROJ Documentation](https://proj.org/)
- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [EPSG Registry](https://epsg.org/)

## Future Scope

### Planned Features
- [ ] Support for GeoJSON files
- [ ] Support for GeoPackage format
- [ ] Batch file upload
- [ ] File download in different formats
- [ ] Geometry validation and repair
- [ ] Visual map display of features
- [ ] Export measurements to CSV/Excel
- [ ] User authentication and file management
- [ ] Advanced spatial queries (intersection, buffer, etc.)
- [ ] Real-time processing status
- [ ] WebSocket support for large files

### Performance Improvements
- [ ] Database integration for persistent storage
- [ ] Asynchronous file processing with Celery
- [ ] Caching layer for frequently accessed files
- [ ] CDN for static assets
- [ ] Horizontal scaling with load balancer

### Security Enhancements
- [ ] JWT authentication
- [ ] Rate limiting
- [ ] File size and type validation
- [ ] Malware scanning
- [ ] Encryption at rest
- [ ] Audit logging

## License

This project is created as a technical assignment for educational purposes.

## Contact

For questions or support, please open an issue on GitHub.
