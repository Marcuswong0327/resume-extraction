import io
from pdf2image import convert_from_bytes
from PIL import Image
import streamlit as st

class PDFProcessor:
    """Handles PDF to image conversion for OCR processing"""
    
    def __init__(self):
        self.dpi = 300  # High DPI for better OCR accuracy
    
    def pdf_to_images(self, uploaded_file):
        """
        Convert PDF file to list of PIL images
        
        Args:
            uploaded_file: Streamlit uploaded file object
            
        Returns:
            List of PIL Image objects
        """
        try:
            # Read PDF bytes
            pdf_bytes = uploaded_file.read()
            
            if not pdf_bytes:
                raise ValueError("PDF file is empty or could not be read")
            
            # Convert PDF to images
            images = convert_from_bytes(
                pdf_bytes,
                dpi=self.dpi,
                output_folder=None,
                thread_count=1,
                fmt='PNG'
            )
            
            if not images:
                raise ValueError("No pages found in PDF file")
            
            # Convert to RGB if necessary (some PDFs might be in CMYK)
            processed_images = []
            for i, image in enumerate(images):
                try:
                    if image.mode != 'RGB':
                        image = image.convert('RGB')
                    
                    # Optimize image for OCR
                    optimized_image = self.optimize_image_for_ocr(image)
                    processed_images.append(optimized_image)
                except Exception as e:
                    st.warning(f"Error processing page {i+1}: {str(e)}")
                    continue
            
            if not processed_images:
                raise ValueError("No pages could be processed from PDF")
            
            return processed_images
            
        except Exception as e:
            st.error(f"Error converting PDF to images: {str(e)}")
            raise e
    
    def optimize_image_for_ocr(self, image):
        """
        Optimize image for better OCR results
        
        Args:
            image: PIL Image object
            
        Returns:
            Optimized PIL Image object
        """
        try:
            # Keep original for now, but could add grayscale conversion if needed
            # Convert to RGB to ensure compatibility
            if image.mode != 'RGB':
                image = image.convert('RGB')
            
            # Resize if image is too large (OCR works better on reasonably sized images)
            width, height = image.size
            max_dimension = 2500  # Increased for better quality
            
            if width > max_dimension or height > max_dimension:
                # Calculate new size maintaining aspect ratio
                if width > height:
                    new_width = max_dimension
                    new_height = int((height * max_dimension) / width)
                else:
                    new_height = max_dimension
                    new_width = int((width * max_dimension) / height)
                
                image = image.resize((new_width, new_height), Image.Resampling.LANCZOS)
            
            return image
            
        except Exception as e:
            st.error(f"Error optimizing image for OCR: {str(e)}")
            return image
    
    def image_to_bytes(self, image, format='PNG'):
        """
        Convert PIL image to bytes for API calls
        
        Args:
            image: PIL Image object
            format: Image format (PNG, JPEG, etc.)
            
        Returns:
            Bytes representation of the image
        """
        try:
            img_byte_arr = io.BytesIO()
            image.save(img_byte_arr, format=format)
            img_byte_arr = img_byte_arr.getvalue()
            return img_byte_arr
            
        except Exception as e:
            st.error(f"Error converting image to bytes: {str(e)}")
            raise e
