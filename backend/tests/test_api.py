import pytest
from fastapi.testclient import TestClient
from pathlib import Path
import sys
import os

# Add parent directory to path to import app
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.main import app

client = TestClient(app)


@pytest.fixture
def sample_kml_file():
    """Path to sample KML file"""
    return Path(__file__).parent.parent / "sample_files" / "sample_chennai.kml"


@pytest.fixture
def sample_shapefile_zip():
    """Path to sample zipped Shapefile"""
    return Path(__file__).parent.parent / "sample_files" / "sample_polygon.zip"


def test_health_check():
    """Test health check endpoint"""
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "healthy", "service": "Geospatial File Measurement API"}


def test_upload_kml(sample_kml_file):
    """Test uploading a KML file"""
    if not sample_kml_file.exists():
        pytest.skip("Sample KML file not found")

    with open(sample_kml_file, "rb") as f:
        response = client.post(
            "/api/files/",
            files={"file": ("sample_chennai.kml", f, "application/vnd.google-earth.kml+xml")}
        )

    assert response.status_code == 200
    data = response.json()
    assert "id" in data
    assert data["filename"] == "sample_chennai.kml"
    assert data["file_type"] == "kml"
    assert data["status"] == "processed"
    assert data["feature_count"] > 0
    assert data["crs"] is not None


def test_upload_shapefile(sample_shapefile_zip):
    """Test uploading a zipped Shapefile"""
    if not sample_shapefile_zip.exists():
        pytest.skip("Sample Shapefile not found")

    with open(sample_shapefile_zip, "rb") as f:
        response = client.post(
            "/api/files/",
            files={"file": ("sample_polygon.zip", f, "application/zip")}
        )

    assert response.status_code == 200
    data = response.json()
    assert "id" in data
    assert data["filename"] == "sample_polygon.zip"
    assert data["file_type"] == "zip"
    assert data["status"] == "processed"
    assert data["feature_count"] > 0
    assert data["crs"] is not None


def test_upload_invalid_file():
    """Test uploading an invalid file type"""
    # Create a fake text file
    import tempfile
    with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
        f.write("This is not a valid geospatial file")
        temp_path = f.name

    try:
        with open(temp_path, "rb") as f:
            response = client.post(
                "/api/files/",
                files={"file": ("test.txt", f, "text/plain")}
            )

        assert response.status_code == 400
        assert "Invalid file type" in response.json()["detail"]
    finally:
        os.unlink(temp_path)


def test_get_file_details(sample_kml_file):
    """Test getting file details"""
    if not sample_kml_file.exists():
        pytest.skip("Sample KML file not found")

    # Upload file first
    with open(sample_kml_file, "rb") as f:
        upload_response = client.post(
            "/api/files/",
            files={"file": ("sample_chennai.kml", f, "application/vnd.google-earth.kml+xml")}
        )
    
    file_id = upload_response.json()["id"]

    response = client.get(f"/api/files/{file_id}/")
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == file_id
    assert data["feature_count"] > 0
    assert len(data["features"]) > 0

    # Check first feature
    first_feature = data["features"][0]
    assert "id" in first_feature
    assert "geometry_type" in first_feature
    assert "geometry" in first_feature
    assert "properties" in first_feature


def test_get_file_not_found():
    """Test getting a non-existent file"""
    response = client.get("/api/files/nonexistent-id/")
    assert response.status_code == 404
    assert "File not found" in response.json()["detail"]


def test_get_measurements(sample_kml_file):
    """Test getting measurements for a file"""
    if not sample_kml_file.exists():
        pytest.skip("Sample KML file not found")

    # Upload file first
    with open(sample_kml_file, "rb") as f:
        upload_response = client.post(
            "/api/files/",
            files={"file": ("sample_chennai.kml", f, "application/vnd.google-earth.kml+xml")}
        )
    
    file_id = upload_response.json()["id"]

    response = client.get(f"/api/files/{file_id}/measurements/")
    assert response.status_code == 200
    data = response.json()
    assert data["file_id"] == file_id
    assert "source_crs" in data
    assert "measurement_crs" in data
    assert len(data["measurements"]) > 0

    # Check first measurement
    first_measurement = data["measurements"][0]
    assert "feature_id" in first_measurement
    assert "geometry_type" in first_measurement
    assert "measurement_type" in first_measurement
    assert "properties" in first_measurement


def test_measurements_crs_transformation(sample_kml_file):
    """Test that CRS transformation is applied for geographic CRS"""
    if not sample_kml_file.exists():
        pytest.skip("Sample KML file not found")

    # Upload file first
    with open(sample_kml_file, "rb") as f:
        upload_response = client.post(
            "/api/files/",
            files={"file": ("sample_chennai.kml", f, "application/vnd.google-earth.kml+xml")}
        )
    
    file_id = upload_response.json()["id"]

    response = client.get(f"/api/files/{file_id}/measurements/")
    data = response.json()

    # If source is geographic (WGS84), measurement CRS should be projected
    if data["source_crs"] and "4326" in data["source_crs"]:
        assert data["measurement_crs"] != data["source_crs"]
        assert "EPSG" in data["measurement_crs"]


def test_measurements_polygon_area(sample_shapefile_zip):
    """Test that polygon area is calculated correctly"""
    if not sample_shapefile_zip.exists():
        pytest.skip("Sample Shapefile not found")

    # Upload file first
    with open(sample_shapefile_zip, "rb") as f:
        upload_response = client.post(
            "/api/files/",
            files={"file": ("sample_polygon.zip", f, "application/zip")}
        )
    
    file_id = upload_response.json()["id"]

    response = client.get(f"/api/files/{file_id}/measurements/")
    data = response.json()

    # Find polygon measurements
    polygon_measurements = [
        m for m in data["measurements"]
        if m["geometry_type"] in ["Polygon", "MultiPolygon"]
    ]

    assert len(polygon_measurements) > 0

    for m in polygon_measurements:
        assert m["measurement_type"] == "area_sqm"
        assert m["measurement"] is not None
        assert m["measurement"] > 0  # Area should be positive


def test_measurements_point_no_measurement(sample_kml_file):
    """Test that points have no measurement"""
    if not sample_kml_file.exists():
        pytest.skip("Sample KML file not found")

    # Upload file first
    with open(sample_kml_file, "rb") as f:
        upload_response = client.post(
            "/api/files/",
            files={"file": ("sample_chennai.kml", f, "application/vnd.google-earth.kml+xml")}
        )
    
    file_id = upload_response.json()["id"]

    response = client.get(f"/api/files/{file_id}/measurements/")
    data = response.json()

    # Find point measurements
    point_measurements = [
        m for m in data["measurements"]
        if m["geometry_type"] in ["Point", "MultiPoint"]
    ]

    if point_measurements:
        for m in point_measurements:
            assert m["measurement_type"] in ["point", "multipoint"]
            assert m["measurement"] is None


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
