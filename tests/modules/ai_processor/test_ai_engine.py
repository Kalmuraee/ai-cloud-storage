"""Tests for AI Engine"""
import pytest
from pathlib import Path
from unittest.mock import Mock, patch
from PIL import Image
import io
import fitz

from app.modules.ai_processor.ai_engine import AIEngine
from app.modules.storage.models import File

@pytest.fixture
def ai_engine():
    return AIEngine()

@pytest.fixture
def mock_file():
    return Mock(spec=File, bucket="test-bucket", path="test.txt")

@pytest.fixture
def text_file(tmp_path):
    file_path = tmp_path / "test.txt"
    file_path.write_text("This is a test document. It contains multiple sentences for testing.")
    return file_path

@pytest.fixture
def image_file(tmp_path):
    file_path = tmp_path / "test.png"
    # Create a simple test image
    img = Image.new('RGB', (100, 100), color='red')
    img.save(file_path)
    return file_path

@pytest.fixture
def pdf_file(tmp_path):
    file_path = tmp_path / "test.pdf"
    # Create a simple PDF
    doc = fitz.open()
    page = doc.new_page()
    page.insert_text((50, 50), "Test PDF document")
    doc.save(str(file_path))
    doc.close()
    return file_path

@pytest.mark.asyncio
async def test_analyze_text(ai_engine, text_file, mock_file, monkeypatch):
    # Mock file path resolution
    monkeypatch.setattr(Path, "__truediv__", lambda self, other: text_file)
    
    # Mock NLP pipeline
    with patch("app.modules.ai_processor.ai_engine.pipeline") as mock_pipeline:
        mock_summarizer = Mock(return_value=[{"summary_text": "Test summary", "score": 0.9}])
        mock_classifier = Mock(return_value=[{"label": "POSITIVE", "score": 0.8}])
        mock_pipeline.side_effect = [mock_summarizer, mock_classifier]
        
        result = await ai_engine.analyze_content(mock_file)
        
        assert result["content_type"] == "text"
        assert result["summary"] == "Test summary"
        assert result["sentiment"]["label"] == "POSITIVE"
        assert result["confidence"] == 0.8  # Min of summary and sentiment scores
        assert "entities" in result
        assert "key_phrases" in result

@pytest.mark.asyncio
async def test_analyze_image(ai_engine, image_file, mock_file, monkeypatch):
    # Mock file path resolution
    monkeypatch.setattr(Path, "__truediv__", lambda self, other: image_file)
    
    # Mock image classifier
    with patch("app.modules.ai_processor.ai_engine.pipeline") as mock_pipeline:
        mock_classifier = Mock(return_value=[
            {"label": "red color", "score": 0.95},
            {"label": "square", "score": 0.8}
        ])
        mock_pipeline.return_value = mock_classifier
        
        result = await ai_engine.analyze_content(mock_file)
        
        assert result["content_type"] == "image"
        assert len(result["classifications"]) > 0
        assert result["dimensions"]["width"] == 100
        assert result["dimensions"]["height"] == 100
        assert result["confidence"] > 0

@pytest.mark.asyncio
async def test_analyze_pdf(ai_engine, pdf_file, mock_file, monkeypatch):
    # Mock file path resolution
    monkeypatch.setattr(Path, "__truediv__", lambda self, other: pdf_file)
    
    # Mock summarizer
    with patch("app.modules.ai_processor.ai_engine.pipeline") as mock_pipeline:
        mock_summarizer = Mock(return_value=[{"summary_text": "Test summary", "score": 0.9}])
        mock_pipeline.return_value = mock_summarizer
        
        result = await ai_engine.analyze_content(mock_file)
        
        assert result["content_type"] == "pdf"
        assert result["page_count"] == 1
        assert result["summary"] == "Test summary"
        assert "images" in result
        assert result["confidence"] > 0

@pytest.mark.asyncio
async def test_extract_metadata(ai_engine, text_file, mock_file, monkeypatch):
    # Mock file path resolution
    monkeypatch.setattr(Path, "__truediv__", lambda self, other: text_file)
    
    result = await ai_engine.extract_metadata(mock_file)
    
    assert "technical" in result
    assert "content" in result
    assert "tags" in result
    assert result["technical"]["mime_type"].startswith("text/")
    assert result["technical"]["size"] > 0
    assert result["confidence"] > 0

@pytest.mark.asyncio
async def test_error_handling(ai_engine, mock_file, monkeypatch):
    # Mock file path to non-existent file
    monkeypatch.setattr(Path, "__truediv__", lambda self, other: Path("/nonexistent"))
    
    result = await ai_engine.analyze_content(mock_file)
    
    assert "error" in result
    assert result["confidence"] == 0.0
