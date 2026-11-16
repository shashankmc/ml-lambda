import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

class TestHealth:
    """Health check tests"""
    
    def test_health_endpoint(self):
        """Test that health endpoint returns OK status"""
        response = client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "ok"
        assert "model" in data
        assert data["model"] is not None

class TestSegmentation:
    """Segmentation endpoint tests"""
    
    def test_segment_rechtspraak(self):
        """Test regex segmentation for Rechtspraak documents"""
        text = """OVERWEGINGEN

De rechtbank overweegt dat de zaak goed is ingesteld.

BESLISSING

De rechtbank beslist:"""
        
        response = client.post("/segment/ml", json={
            "text": text,
            "source": "rechtspraak"
        })
        
        assert response.status_code == 200
        data = response.json()
        assert "segments" in data
        assert len(data["segments"]) > 0
        
        # Check for expected segment types
        types = {seg["segment_type"] for seg in data["segments"]}
        assert "considerations" in types or "decision" in types

    def test_segment_unknown_source(self):
        """Test segmentation with unknown source defaults to paragraph"""
        text = "Line 1\n\nLine 2\n\nLine 3"
        
        response = client.post("/segment/ml", json={
            "text": text,
            "source": "unknown_source"
        })
        
        assert response.status_code == 200
        data = response.json()
        assert "segments" in data

    def test_segment_empty_text(self):
        """Test segmentation with empty text"""
        response = client.post("/segment/ml", json={
            "text": "",
            "source": "rechtspraak"
        })
        
        assert response.status_code == 200
        data = response.json()
        assert "segments" in data

class TestSummarization:
    """Summarization endpoint tests (requires DB setup)"""
    
    @pytest.mark.skip(reason="Requires database setup")
    def test_summarize_on_demand(self):
        """Test on-demand summarization"""
        response = client.post("/summarize", json={
            "case_id": 1,
            "ecli": "ECLI:NL:TEST:001",
            "source": "test",
            "caller": "on_demand"
        })
        
        assert response.status_code in [200, 404]  # 404 if case doesn't exist

    def test_summarize_invalid_input(self):
        """Test summarization with invalid input"""
        response = client.post("/summarize", json={
            "case_id": "invalid",  # Should be int
            "ecli": "TEST"
        })
        
        assert response.status_code == 422  # Validation error

class TestStatus:
    """Status check endpoint tests"""
    
    def test_status_nonexistent_job(self):
        """Test status check for non-existent job"""
        response = client.get("/status/00000000-0000-0000-0000-000000000000")
        
        assert response.status_code == 404
        data = response.json()
        assert "not found" in data.get("detail", "").lower()

if __name__ == "__main__":
    pytest.main([__file__, "-v"])
