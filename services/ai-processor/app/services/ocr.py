from PIL import Image
import pytesseract
import io
import pdf2image
from typing import List

class OCRService:
    def __init__(self):
        # Configure Tesseract if needed
        pass

    async def extract_text_from_image(self, image_data: bytes) -> str:
        """Extract text from image using OCR."""
        try:
            # Convert bytes to PIL Image
            image = Image.open(io.BytesIO(image_data))
            # Perform OCR
            text = pytesseract.image_to_string(image)
            return text
        except Exception as e:
            raise Exception(f"Failed to extract text from image: {str(e)}")

    async def extract_text_from_pdf_with_ocr(self, pdf_data: bytes) -> str:
        """Extract text from PDF using OCR if needed."""
        try:
            # Convert PDF to images
            images = pdf2image.convert_from_bytes(pdf_data)
            texts = []
            
            # Process each page
            for image in images:
                # Convert PIL image to bytes
                img_byte_arr = io.BytesIO()
                image.save(img_byte_arr, format='PNG')
                img_byte_arr = img_byte_arr.getvalue()
                
                # Extract text using OCR
                text = await self.extract_text_from_image(img_byte_arr)
                texts.append(text)
            
            return "\n\n".join(texts)
        except Exception as e:
            raise Exception(f"Failed to extract text from PDF with OCR: {str(e)}")

ocr_service = OCRService()