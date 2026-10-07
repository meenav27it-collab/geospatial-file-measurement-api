from pydantic import BaseModel
from typing import List, Optional, Dict, Any


class FileUploadResponse(BaseModel):
    id: str
    filename: str
    file_type: str
    status: str
    feature_count: int
    crs: Optional[str] = None


class Feature(BaseModel):
    id: int
    geometry_type: Optional[str] = None
    geometry: Optional[str] = None
    properties: Dict[str, Any] = {}


class FileDetailResponse(BaseModel):
    id: str
    filename: str
    file_type: str
    crs: Optional[str] = None
    feature_count: int
    features: List[Feature]


class FeatureMeasurement(BaseModel):
    feature_id: int
    geometry_type: Optional[str] = None
    measurement: Optional[float] = None
    measurement_type: Optional[str] = None
    properties: Dict[str, Any] = {}


class MeasurementResponse(BaseModel):
    file_id: str
    source_crs: Optional[str] = None
    measurement_crs: str
    measurements: List[FeatureMeasurement]
