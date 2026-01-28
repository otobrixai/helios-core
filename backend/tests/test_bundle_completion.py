import io
import zipfile
import pytest
from datetime import datetime
from uuid import uuid4

from backend.tools.generate_bundle import generate_supplementary_bundle
from backend.models.entities import (
    Analysis, AnalysisMode, AnalysisStatus, ExtractedParameters,
    Measurement, MeasurementMetadata, SolverConfig, ModelType
)

@pytest.fixture
def mock_entities():
    # Mock Measurement
    measurement = Measurement(
        id=uuid4(),
        import_record_id=uuid4(),
        device_label="Test_Device_01",
        raw_data_path="test_data.csv",
        metadata=MeasurementMetadata(
            cell_area_cm2=0.1,
            temperature_c=25.0
        )
    )
    
    # Mock Parameters
    params = ExtractedParameters(
        j_sc=20.5,
        v_oc=0.74,
        ff=0.80,
        pce=22.1,
        r_s=1.5,
        r_sh=1000.0,
        n_ideality=1.1,
        i_ph=0.002,
        i_0=1e-12
    )
    
    # Mock Analysis
    analysis = Analysis(
        id=uuid4(),
        measurement_id=measurement.id,
        timestamp=datetime.utcnow(),
        mode=AnalysisMode.REFERENCE,
        status=AnalysisStatus.VALID,
        solver_config=SolverConfig(model_type=ModelType.ONE_DIODE),
        parameters=params,
        result_hash="abc123hash",
        masks_applied=[]
    )
    
    return analysis, measurement

def test_generate_bundle_includes_new_artifacts(mock_entities, tmp_path):
    """Verify that bundle contains PDF, SVG, and LaTeX files."""
    analysis, measurement = mock_entities
    
    # Mock raw data file creation since ingest_file isn't actually called
    # We need to ensure the raw file fetcher in generate_bundle finds something
    # However, since generate_bundle imports extract_iv_data which reads file
    # We'll need to mock extract_iv_data or provide a real file.
    # For this unit test, simpler to mock the data extraction if possible,
    # OR create a dummy file at the expected path.
    
    # To test integration properly, we can mock the extract_iv_data function
    # inside generate_bundle to return dummy V, I arrays.
    
    with pytest.MonkeyPatch.context() as m:
        # Mock extract_iv_data to avoid file I/O
        import numpy as np
        
        def mock_extract_iv_data(*args, **kwargs):
            V = np.linspace(0, 0.8, 50)
            I = 0.02 * (1 - np.exp((V - 0.74)/0.026)) 
            return V, I
            
        m.setattr("backend.tools.generate_bundle.extract_iv_data", mock_extract_iv_data)
        
        # Override EXPORTS_DIR to use tmp_path
        m.setattr("backend.tools.generate_bundle.EXPORTS_DIR", tmp_path)
        
        # Run generation
        bundle_path = generate_supplementary_bundle(analysis, measurement)
        
        # Verify
        assert bundle_path.exists()
        
        with zipfile.ZipFile(bundle_path, "r") as zf:
            files = zf.namelist()
            print(f"Generated files: {files}")
            
            assert "report.pdf" in files
            assert "report.svg" in files
            assert "results.tex" in files
            assert "audit.json" in files
            assert "results.csv" in files
            
            # Additional Content Checks
            tex_content = zf.read("results.tex").decode("utf-8")
            assert "\\begin{tabular}" in tex_content
            assert "$J_{sc}$" in tex_content
            assert "20.5000" in tex_content  # Value check
            
            # PDF validation (header check)
            pdf_header = zf.read("report.pdf")[:4]
            assert pdf_header == b"%PDF"
            
            # SVG validation
            svg_content = zf.read("report.svg").decode("utf-8")
            assert "<svg" in svg_content
