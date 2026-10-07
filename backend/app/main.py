from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
import os
import shutil
from pathlib import Path
from typing import List, Optional
import uuid
import pandas as pd
from .models import FileUploadResponse, FileDetailResponse, MeasurementResponse, FeatureMeasurement
from .geo_processor import GeoProcessor
from .crs_handler import CRSHandler

app = FastAPI(
    title="Geospatial File Measurement API",
    description="API for uploading and measuring geospatial files (KML, Shapefile)",
    version="1.0.0"
)

# CORS configuration
origins = [
    "http://localhost:5173",
    "http://localhost:3000",
    "http://localhost:8000",
    "http://127.0.0.1:5173",
    "http://127.0.0.1:3000",
    "http://127.0.0.1:8000",
    "*",  # Allow all origins for testing (remove in production)
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Create necessary directories
UPLOAD_DIR = Path("uploads")
UPLOAD_DIR.mkdir(exist_ok=True)

# Serve static files (frontend)
FRONTEND_DIR = Path("../frontend/dist")
if FRONTEND_DIR.exists():
    if (FRONTEND_DIR / "static").exists():
        app.mount("/static", StaticFiles(directory=str(FRONTEND_DIR / "static")), name="static")
    elif (FRONTEND_DIR / "assets").exists():
        app.mount("/assets", StaticFiles(directory=str(FRONTEND_DIR / "assets")), name="assets")

# In-memory storage for files (for demo purposes)
file_storage = {}

# Initialize processors
geo_processor = GeoProcessor()
crs_handler = CRSHandler()


@app.get("/health")
def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "service": "Geospatial File Measurement API"}


@app.post("/api/files/", response_model=FileUploadResponse)
async def upload_file(file: UploadFile = File(...)):
    """
    Upload a geospatial file (KML or zipped Shapefile)
    """
    import logging
    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger(__name__)
    
    logger.info(f"Received file upload request: {file.filename}")
    logger.info(f"File content type: {file.content_type}")
    
    # Validate file extension
    allowed_extensions = ['.kml', '.zip']
    file_ext = Path(file.filename).suffix.lower()
    
    logger.info(f"File extension: {file_ext}")
    
    if file_ext not in allowed_extensions:
        logger.error(f"Invalid file type: {file_ext}")
        raise HTTPException(
            status_code=400,
            detail=f"Invalid file type. Allowed types: {', '.join(allowed_extensions)}"
        )
    
    # Generate unique ID
    file_id = str(uuid.uuid4())
    logger.info(f"Generated file ID: {file_id}")
    
    # Save uploaded file
    file_path = UPLOAD_DIR / f"{file_id}{file_ext}"
    logger.info(f"Saving file to: {file_path}")
    
    try:
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        logger.info(f"File saved successfully")
    except Exception as e:
        logger.error(f"Failed to save file: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to save file: {str(e)}")
    
    # Process the file
    try:
        logger.info(f"Processing file with {file_ext} format")
        gdf = geo_processor.read_file(file_path, file_ext)
        logger.info(f"File processed successfully, {len(gdf)} features found")
        
        # Store file info
        file_storage[file_id] = {
            "filename": file.filename,
            "file_path": str(file_path),
            "file_type": file_ext,
            "gdf": gdf,
            "crs": str(gdf.crs) if gdf.crs else None,
            "feature_count": len(gdf)
        }
        
        logger.info(f"Returning response for file {file_id}")
        return FileUploadResponse(
            id=file_id,
            filename=file.filename,
            file_type=file_ext[1:],  # Remove the dot
            status="processed",
            feature_count=len(gdf),
            crs=str(gdf.crs) if gdf.crs else None
        )
    except Exception as e:
        logger.error(f"Failed to process file: {str(e)}")
        # Clean up file if processing fails
        if file_path.exists():
            file_path.unlink()
        raise HTTPException(status_code=422, detail=f"Failed to process file: {str(e)}")


@app.get("/api/files/{file_id}/", response_model=FileDetailResponse)
async def get_file(file_id: str):
    """
    Get details of an uploaded file
    """
    if file_id not in file_storage:
        raise HTTPException(status_code=404, detail="File not found")
    
    file_info = file_storage[file_id]
    gdf = file_info["gdf"]
    
    # Extract features
    features = []
    for idx, row in gdf.iterrows():
        # Convert properties to JSON-serializable types
        properties = {}
        for k, v in row.items():
            if k != 'geometry':
                # Handle NaN values and non-serializable types
                if pd.isna(v):
                    properties[k] = None
                elif isinstance(v, (int, float, str, bool)):
                    properties[k] = v
                else:
                    properties[k] = str(v)
        
        feature = {
            "id": int(idx),
            "geometry_type": str(row.geometry.geom_type) if row.geometry else None,
            "geometry": str(row.geometry) if row.geometry else None,
            "properties": properties
        }
        features.append(feature)
    
    return FileDetailResponse(
        id=file_id,
        filename=file_info["filename"],
        file_type=file_info["file_type"][1:],
        crs=file_info["crs"],
        feature_count=len(gdf),
        features=features
    )


@app.get("/api/files/{file_id}/measurements/", response_model=MeasurementResponse)
async def get_measurements(file_id: str):
    """
    Get measurements for all features in a file
    """
    if file_id not in file_storage:
        raise HTTPException(status_code=404, detail="File not found")
    
    file_info = file_storage[file_id]
    gdf = file_info["gdf"]
    source_crs = file_info["crs"]
    
    # Determine appropriate projected CRS
    projected_crs = crs_handler.get_projected_crs(gdf)
    
    # Transform if needed
    if projected_crs != source_crs:
        gdf_projected = gdf.to_crs(projected_crs)
    else:
        gdf_projected = gdf
    
    # Calculate measurements
    measurements = []
    for idx, row in gdf_projected.iterrows():
        geom = row.geometry
        geom_type = geom.geom_type if geom else None
        
        measurement = None
        measurement_type = None
        
        if geom_type == "Polygon":
            measurement = geom.area  # Area in square meters
            measurement_type = "area_sqm"
        elif geom_type == "MultiPolygon":
            measurement = geom.area  # Area in square meters
            measurement_type = "area_sqm"
        elif geom_type == "LineString":
            measurement = geom.length  # Length in meters
            measurement_type = "length_m"
        elif geom_type == "MultiLineString":
            measurement = geom.length  # Length in meters
            measurement_type = "length_m"
        elif geom_type == "Point":
            measurement = None
            measurement_type = "point"
        elif geom_type == "MultiPoint":
            measurement = None
            measurement_type = "multipoint"
        else:
            measurement = None
            measurement_type = "unsupported"
        
        # Convert properties to JSON-serializable types
        properties = {}
        for k, v in row.items():
            if k != 'geometry':
                if pd.isna(v):
                    properties[k] = None
                elif isinstance(v, (int, float, str, bool)):
                    properties[k] = v
                else:
                    properties[k] = str(v)
        
        feature_measurement = FeatureMeasurement(
            feature_id=int(idx),
            geometry_type=geom_type,
            measurement=measurement,
            measurement_type=measurement_type,
            properties=properties
        )
        measurements.append(feature_measurement)
    
    return MeasurementResponse(
        file_id=file_id,
        source_crs=source_crs,
        measurement_crs=projected_crs,
        measurements=measurements
    )


@app.get("/")
async def serve_frontend():
    """Serve the frontend dashboard"""
    frontend_path = FRONTEND_DIR / "index.html"
    if frontend_path.exists():
        return FileResponse(frontend_path)
    return {"message": "Geospatial File Measurement API. Visit /docs for Swagger documentation."}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
