"""PDF processing module for converting PDF to images."""

import io
import logging
from pathlib import Path
from typing import List

import fitz  # PyMuPDF
from PIL import Image

logger = logging.getLogger(__name__)


class PDFProcessor:
    """Handles PDF to image conversion."""
    
    def __init__(self, dpi: int = 200):
        self.dpi = dpi
    
    def convert_to_images(self, pdf_path: str, output_dir: Path) -> List[str]:
        """Convert PDF pages to PNG images using PyMuPDF."""
        logger.info(f"Converting {pdf_path} to images...")
        
        if not Path(pdf_path).exists():
            raise FileNotFoundError(f"PDF file not found: {pdf_path}")
        
        output_dir.mkdir(parents=True, exist_ok=True)
        
        # Open PDF with PyMuPDF
        doc = fitz.open(pdf_path)
        
        image_paths = []
        for page_num in range(len(doc)):
            page = doc.load_page(page_num)
            
            # Create transformation matrix for DPI scaling
            mat = fitz.Matrix(self.dpi / 72, self.dpi / 72)
            
            # Render page to pixmap
            pix = page.get_pixmap(matrix=mat)
            
            # Convert to PIL Image and save
            img_data = pix.tobytes("png")
            img = Image.open(io.BytesIO(img_data))
            
            image_path = output_dir / f"slide_{page_num + 1:02d}.png"
            img.save(image_path, 'PNG')
            image_paths.append(str(image_path))
            logger.info(f"Saved slide {page_num + 1} to {image_path}")
        
        doc.close()
        return image_paths 