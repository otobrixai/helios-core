import requests
import json
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_citation_generation():
    url = "http://localhost:8001/api/stateless/analyze"
    
    payload = {
        "device_label": "test_device",
        "voltage": [0.0, 0.1, 0.2, 0.3, 0.4, 0.5, 0.6],
        "current": [0.02, 0.02, 0.02, 0.019, 0.015, 0.005, 0.0],
        "area_cm2": 1.0,
        "temperature_k": 300,
        "mode": "Reference",
        "model_type": "OneDiode"
    }
    
    try:
        logger.info("Sending request to stateless Analyze API...")
        response = requests.post(url, json=payload)
        response.raise_for_status()
        
        data = response.json()
        
        logger.info("Response received.")
        
        audit_id = data.get("audit_id")
        bibtex = data.get("bibtex")
        
        if audit_id:
            logger.info(f"SUCCESS: Audit ID found: {audit_id}")
        else:
            logger.error("FAILURE: Audit ID missing from response.")
            
        if bibtex:
            logger.info(f"SUCCESS: BibTeX entry found:\n{bibtex}")
        else:
            logger.error("FAILURE: BibTeX entry missing from response.")
            
        if audit_id and bibtex:
            print("\nVERIFICATION PASSED: Citation Engine is active.")
        else:
            print("\nVERIFICATION FAILED: Missing fields.")
            
    except Exception as e:
        logger.error(f"Test failed with error: {e}")
        if hasattr(e, 'response') and e.response:
            logger.error(f"Response content: {e.response.text}")

if __name__ == "__main__":
    test_citation_generation()
