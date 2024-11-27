"""
AI Engine for content analysis and metadata extraction
"""
from typing import Dict, Any, List, Optional
import mimetypes
import magic
import spacy
from transformers import pipeline
from PIL import Image
import pytesseract
import fitz  # PyMuPDF
import numpy as np
from pathlib import Path

from app.core.logging import get_logger
from app.core.config import settings
from app.modules.storage.models import File

logger = get_logger(__name__)

class AIEngine:
    """Engine for AI-powered content analysis"""
    
    def __init__(self):
        # Load models lazily
        self._nlp = None
        self._summarizer = None
        self._classifier = None
        self._image_classifier = None
        
    @property
    def nlp(self):
        """Get or load spaCy model"""
        if self._nlp is None:
            self._nlp = spacy.load("en_core_web_sm")
        return self._nlp
        
    @property
    def summarizer(self):
        """Get or load summarization model"""
        if self._summarizer is None:
            self._summarizer = pipeline(
                "summarization",
                model="facebook/bart-large-cnn",
                device=-1  # CPU
            )
        return self._summarizer
        
    @property
    def classifier(self):
        """Get or load text classification model"""
        if self._classifier is None:
            self._classifier = pipeline(
                "text-classification",
                model="distilbert-base-uncased-finetuned-sst-2-english",
                device=-1  # CPU
            )
        return self._classifier
        
    @property
    def image_classifier(self):
        """Get or load image classification model"""
        if self._image_classifier is None:
            self._image_classifier = pipeline(
                "image-classification",
                model="google/vit-base-patch16-224",
                device=-1  # CPU
            )
        return self._image_classifier

    async def analyze_content(self, file: File) -> Dict[str, Any]:
        """
        Analyze file content using appropriate AI models
        
        Args:
            file: File object to analyze
            
        Returns:
            Dict containing analysis results
        """
        try:
            # Get file path
            file_path = Path(settings.MINIO_DATA_DIR) / file.bucket / file.path
            
            # Detect content type
            mime_type = magic.from_file(str(file_path), mime=True)
            
            # Process based on content type
            if mime_type.startswith('text/'):
                return await self._analyze_text(file_path)
            elif mime_type.startswith('image/'):
                return await self._analyze_image(file_path)
            elif mime_type == 'application/pdf':
                return await self._analyze_pdf(file_path)
            else:
                return {
                    'content_type': mime_type,
                    'analysis': 'Unsupported file type',
                    'confidence': 1.0
                }
                
        except Exception as e:
            logger.error(f"Failed to analyze content: {str(e)}")
            return {
                'error': str(e),
                'confidence': 0.0
            }

    async def extract_metadata(self, file: File) -> Dict[str, Any]:
        """
        Extract metadata from file
        
        Args:
            file: File object to process
            
        Returns:
            Dict containing metadata
        """
        try:
            # Get file path
            file_path = Path(settings.MINIO_DATA_DIR) / file.bucket / file.path
            
            # Get basic file info
            stat = file_path.stat()
            mime_type = magic.from_file(str(file_path), mime=True)
            
            metadata = {
                'technical': {
                    'mime_type': mime_type,
                    'size': stat.st_size,
                    'created': stat.st_ctime,
                    'modified': stat.st_mtime
                },
                'content': {},
                'tags': [],
                'confidence': 0.9
            }
            
            # Extract content-specific metadata
            if mime_type.startswith('text/'):
                text_meta = await self._extract_text_metadata(file_path)
                metadata['content'].update(text_meta)
            elif mime_type.startswith('image/'):
                image_meta = await self._extract_image_metadata(file_path)
                metadata['content'].update(image_meta)
            elif mime_type == 'application/pdf':
                pdf_meta = await self._extract_pdf_metadata(file_path)
                metadata['content'].update(pdf_meta)
                
            return metadata
                
        except Exception as e:
            logger.error(f"Failed to extract metadata: {str(e)}")
            return {
                'error': str(e),
                'confidence': 0.0
            }

    async def _analyze_text(self, file_path: Path) -> Dict[str, Any]:
        """Analyze text content"""
        with open(file_path, 'r') as f:
            text = f.read()
            
        # Get summary
        summary = self.summarizer(text[:1024], max_length=130, min_length=30)[0]
        
        # Get sentiment
        sentiment = self.classifier(text[:512])[0]
        
        # Extract entities
        doc = self.nlp(text[:5000])  # Limit text length for performance
        entities = [
            {
                'text': ent.text,
                'label': ent.label_,
                'start': ent.start_char,
                'end': ent.end_char
            }
            for ent in doc.ents
        ]
        
        # Extract key phrases
        phrases = [chunk.text for chunk in doc.noun_chunks][:10]
        
        return {
            'content_type': 'text',
            'summary': summary['summary_text'],
            'sentiment': {
                'label': sentiment['label'],
                'score': sentiment['score']
            },
            'entities': entities,
            'key_phrases': phrases,
            'confidence': min(summary['score'], sentiment['score'])
        }

    async def _analyze_image(self, file_path: Path) -> Dict[str, Any]:
        """Analyze image content"""
        # Load image
        image = Image.open(file_path)
        
        # Get classifications
        predictions = self.image_classifier(image)
        
        # Extract text if present
        try:
            text = pytesseract.image_to_string(image)
        except:
            text = ""
        
        return {
            'content_type': 'image',
            'classifications': [
                {
                    'label': p['label'],
                    'confidence': p['score']
                }
                for p in predictions[:5]  # Top 5 predictions
            ],
            'dimensions': {
                'width': image.width,
                'height': image.height
            },
            'extracted_text': text if text.strip() else None,
            'confidence': predictions[0]['score'] if predictions else 0.0
        }

    async def _analyze_pdf(self, file_path: Path) -> Dict[str, Any]:
        """Analyze PDF content"""
        doc = fitz.open(file_path)
        
        # Extract text from first few pages
        text = ""
        for page in doc[:3]:  # First 3 pages
            text += page.get_text()
            
        # Get summary if enough text
        summary = None
        if len(text) > 100:
            summary = self.summarizer(text[:1024], max_length=130, min_length=30)[0]
            
        # Extract images from first page
        images = []
        page = doc[0]
        for img in page.get_images():
            try:
                xref = img[0]
                base = doc.extract_image(xref)
                if base:
                    images.append({
                        'size': base["size"],
                        'extension': base["ext"]
                    })
            except:
                continue
                
        return {
            'content_type': 'pdf',
            'page_count': len(doc),
            'summary': summary['summary_text'] if summary else None,
            'images': images,
            'confidence': summary['score'] if summary else 0.8
        }

    async def _extract_text_metadata(self, file_path: Path) -> Dict[str, Any]:
        """Extract metadata from text file"""
        with open(file_path, 'r') as f:
            text = f.read()
            
        # Analyze with spaCy
        doc = self.nlp(text[:5000])
        
        return {
            'language': doc.lang_,
            'word_count': len(doc),
            'sentence_count': len(list(doc.sents)),
            'readability_score': self._compute_readability(doc)
        }

    async def _extract_image_metadata(self, file_path: Path) -> Dict[str, Any]:
        """Extract metadata from image file"""
        image = Image.open(file_path)
        
        return {
            'format': image.format,
            'mode': image.mode,
            'dimensions': {
                'width': image.width,
                'height': image.height
            },
            'dpi': image.info.get('dpi'),
            'has_exif': hasattr(image, '_getexif') and image._getexif() is not None
        }

    async def _extract_pdf_metadata(self, file_path: Path) -> Dict[str, Any]:
        """Extract metadata from PDF file"""
        doc = fitz.open(file_path)
        
        return {
            'title': doc.metadata.get('title'),
            'author': doc.metadata.get('author'),
            'subject': doc.metadata.get('subject'),
            'keywords': doc.metadata.get('keywords'),
            'page_count': len(doc),
            'version': doc.version
        }

    def _compute_readability(self, doc) -> float:
        """Compute simple readability score"""
        word_count = len(doc)
        sentence_count = len(list(doc.sents))
        
        if sentence_count == 0:
            return 0.0
            
        avg_words_per_sentence = word_count / sentence_count
        return max(0.0, min(1.0, 1.0 - (avg_words_per_sentence - 15) / 25))
