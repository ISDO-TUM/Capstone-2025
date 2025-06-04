import logging
from typing import Optional
from PyPDF2 import PdfReader
from io import BytesIO

logger = logging.getLogger(__name__)

def _extract_text_from_pdf(pdf_content: bytes) -> Optional[str]:
    """
    Extract text from a PDF file.
    
    Args:
        pdf_content (bytes): The PDF file content as bytes
        
    Returns:
        Optional[str]: The extracted text, or None if extraction failed
    """
    try:
        pdf_file = BytesIO(pdf_content)
        pdf_reader = PdfReader(pdf_file)
        text = ""
        for page in pdf_reader.pages:
            text += page.extract_text() + "\n"
            
        return text.strip()
    except Exception as e:
        logger.error(f"Error extracting text from PDF: {e}")
        return None

def enhance_user_profile(project_description: str, paper_text: str, paper_context: str) -> str:
    """
    Enhance the user profile by incorporating the uploaded paper's text and context.
    
    Args:
        project_description (str): The original project description
        paper_text (str): The extracted text from the uploaded paper
        paper_context (str): The user's comment/context about the paper
        
    Returns:
        str: Enhanced user profile combining all information
    """
    # Truncate paper text to roughly 4000 characters (approximately 1000 tokens)
    # This leaves room for the project description, context, and other text
    truncated_paper_text = paper_text[:4000] + "..." if len(paper_text) > 4000 else paper_text
    
    enhanced_profile = f"""
The user has provided an additional paper to better understand their research interests. Here is the context they provided for this paper:
"{paper_context}"

Here is the beginning of the provided paper (truncated for length):
{truncated_paper_text}
"""
    return enhanced_profile.strip()

def process_user_paper(pdf_content: bytes, paper_context: str, project_description: str) -> Optional[str]:
    """
    Process a user-uploaded paper and enhance the user profile.
    
    Args:
        pdf_content (bytes): The PDF file content as bytes
        paper_context (str): The user's comment/context about the paper
        project_description (str): The original project description
        
    Returns:
        Optional[str]: Enhanced user profile, or None if processing failed
    """
    logger.info("Starting paper processing and profile enhancement")
    
    paper_text = _extract_text_from_pdf(pdf_content)
    if not paper_text:
        logger.error("Failed to extract text from PDF")
        return None
        
    logger.info(f"Successfully extracted {len(paper_text)} characters from PDF")
    logger.debug(f"Paper context length: {len(paper_context)} characters")
    logger.debug(f"Original project description length: {len(project_description)} characters")
        
    enhanced_profile = enhance_user_profile(project_description, paper_text, paper_context)
    logger.info(f"Successfully created enhanced profile with total length: {len(enhanced_profile)} characters")
    return enhanced_profile 