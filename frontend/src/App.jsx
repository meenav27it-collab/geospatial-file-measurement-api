import React, { useState, useCallback } from 'react';
import axios from 'axios';
import './App.css';

function App() {
  const [file, setFile] = useState(null);
  const [uploadStatus, setUploadStatus] = useState('');
  const [fileInfo, setFileInfo] = useState(null);
  const [measurements, setMeasurements] = useState(null);
  const [loading, setLoading] = useState(false);
  const [dragActive, setDragActive] = useState(false);

  const API_BASE_URL = window.location.origin;

  const handleDrag = useCallback((e) => {
    e.preventDefault();
    e.stopPropagation();
    if (e.type === 'dragenter' || e.type === 'dragover') {
      setDragActive(true);
    } else if (e.type === 'dragleave') {
      setDragActive(false);
    }
  }, []);

  const handleDrop = useCallback((e) => {
    e.preventDefault();
    e.stopPropagation();
    setDragActive(false);

    if (e.dataTransfer.files && e.dataTransfer.files[0]) {
      setFile(e.dataTransfer.files[0]);
    }
  }, []);

  const handleFileChange = (e) => {
    if (e.target.files && e.target.files[0]) {
      setFile(e.target.files[0]);
    }
  };

  const handleUpload = async () => {
    if (!file) {
      setUploadStatus('Please select a file first');
      return;
    }

    setLoading(true);
    setUploadStatus('Uploading...');
    setFileInfo(null);
    setMeasurements(null);

    const formData = new FormData();
    formData.append('file', file);

    console.log('Starting upload to:', `${API_BASE_URL}/api/files/`);
    console.log('File:', file.name, file.size, file.type);

    try {
      const response = await axios.post(`${API_BASE_URL}/api/files/`, formData, {
        headers: {
          // Don't set Content-Type manually - axios will set it with the correct boundary
        },
        timeout: 30000, // 30 second timeout
      });

      console.log('Upload successful:', response.data);
      setFileInfo(response.data);
      setUploadStatus('File uploaded successfully!');

      // Fetch measurements
      console.log('Fetching measurements...');
      const measurementsResponse = await axios.get(
        `${API_BASE_URL}/api/files/${response.data.id}/measurements/`,
        { timeout: 30000 }
      );
      console.log('Measurements received:', measurementsResponse.data);
      setMeasurements(measurementsResponse.data);
    } catch (error) {
      console.error('Upload error:', error);
      console.error('Error response:', error.response);
      console.error('Error message:', error.message);
      console.error('Error code:', error.code);
      
      let errorMessage = 'Upload failed';
      if (error.code === 'ECONNREFUSED') {
        errorMessage = 'Cannot connect to server. Is the backend running?';
      } else if (error.code === 'ERR_NETWORK') {
        errorMessage = 'Network error. Check CORS configuration.';
      } else if (error.response) {
        errorMessage = `Server error: ${error.response.status} - ${error.response.data?.detail || error.response.statusText}`;
      } else if (error.message) {
        errorMessage = error.message;
      }
      
      setUploadStatus(`Error: ${errorMessage}`);
    } finally {
      setLoading(false);
    }
  };

  const formatMeasurement = (value, type) => {
    if (value === null || value === undefined) {
      return 'N/A';
    }
    if (type === 'area_sqm') {
      return `${value.toLocaleString(undefined, { maximumFractionDigits: 2 })} m²`;
    }
    if (type === 'length_m') {
      return `${value.toLocaleString(undefined, { maximumFractionDigits: 2 })} m`;
    }
    return value;
  };

  return (
    <div className="app">
      <header className="app-header">
        <h1>Geospatial File Measurement API</h1>
        <p>Upload KML or zipped Shapefile to analyze features and measurements</p>
      </header>

      <main className="app-main">
        {/* Upload Section */}
        <section className="upload-section">
          <div
            className={`drop-zone ${dragActive ? 'active' : ''}`}
            onDragEnter={handleDrag}
            onDragLeave={handleDrag}
            onDragOver={handleDrag}
            onDrop={handleDrop}
          >
            <input
              type="file"
              id="fileInput"
              accept=".kml,.zip"
              onChange={handleFileChange}
              style={{ display: 'none' }}
            />
            <label htmlFor="fileInput" className="drop-zone-label">
              <div className="drop-zone-content">
                <svg
                  className="upload-icon"
                  fill="none"
                  stroke="currentColor"
                  viewBox="0 0 24 24"
                >
                  <path
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    strokeWidth={2}
                    d="M7 16a4 4 0 01-.88-7.903A5 5 0 1115.9 6L16 6a5 5 0 011 9.9M15 13l-3-3m0 0l-3 3m3-3v12"
                  />
                </svg>
                <p>Drag and drop a file here, or click to select</p>
                <p className="file-types">Supported: .kml, .zip (Shapefile)</p>
              </div>
            </label>
          </div>

          {file && (
            <div className="selected-file">
              <span className="file-name">{file.name}</span>
              <span className="file-size">
                ({(file.size / 1024).toFixed(2)} KB)
              </span>
            </div>
          )}

          <button
            className="upload-button"
            onClick={handleUpload}
            disabled={!file || loading}
          >
            {loading ? 'Processing...' : 'Upload & Analyze'}
          </button>

          {uploadStatus && (
            <div className={`status-message ${uploadStatus.includes('Error') ? 'error' : 'success'}`}>
              {uploadStatus}
            </div>
          )}
        </section>

        {/* File Information Section */}
        {fileInfo && (
          <section className="info-section">
            <h2>File Information</h2>
            <div className="info-grid">
              <div className="info-item">
                <span className="info-label">Filename:</span>
                <span className="info-value">{fileInfo.filename}</span>
              </div>
              <div className="info-item">
                <span className="info-label">File Type:</span>
                <span className="info-value">{fileInfo.file_type.toUpperCase()}</span>
              </div>
              <div className="info-item">
                <span className="info-label">Feature Count:</span>
                <span className="info-value">{fileInfo.feature_count}</span>
              </div>
              <div className="info-item">
                <span className="info-label">Source CRS:</span>
                <span className="info-value">{fileInfo.crs || 'Unknown'}</span>
              </div>
              <div className="info-item">
                <span className="info-label">Status:</span>
                <span className="info-value success">{fileInfo.status}</span>
              </div>
            </div>
          </section>
        )}

        {/* Measurements Section */}
        {measurements && (
          <section className="measurements-section">
            <h2>Measurements</h2>
            <div className="crs-info">
              <div className="crs-item">
                <span className="crs-label">Source CRS:</span>
                <span className="crs-value">{measurements.source_crs || 'Unknown'}</span>
              </div>
              <div className="crs-item">
                <span className="crs-label">Measurement CRS:</span>
                <span className="crs-value">{measurements.measurement_crs}</span>
              </div>
            </div>

            <div className="table-container">
              <table className="measurements-table">
                <thead>
                  <tr>
                    <th>Feature ID</th>
                    <th>Geometry Type</th>
                    <th>Measurement Type</th>
                    <th>Measurement</th>
                    <th>Properties</th>
                  </tr>
                </thead>
                <tbody>
                  {measurements.measurements.map((m) => (
                    <tr key={m.feature_id}>
                      <td>{m.feature_id}</td>
                      <td>{m.geometry_type || 'N/A'}</td>
                      <td>{m.measurement_type || 'N/A'}</td>
                      <td>{formatMeasurement(m.measurement, m.measurement_type)}</td>
                      <td>
                        {Object.keys(m.properties).length > 0 ? (
                          <details>
                            <summary>{Object.keys(m.properties).length} properties</summary>
                            <div className="properties-details">
                              {Object.entries(m.properties).map(([key, value]) => (
                                <div key={key}>
                                  <strong>{key}:</strong> {String(value)}
                                </div>
                              ))}
                            </div>
                          </details>
                        ) : (
                          'None'
                        )}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </section>
        )}
      </main>

      <footer className="app-footer">
        <p>
          Built with FastAPI, GeoPandas, Shapely, PyProj, and React
        </p>
      </footer>
    </div>
  );
}

export default App;
