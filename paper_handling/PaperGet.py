import requests
import fitz  # PyMuPDF
import io

def fullpaper_get(url):
    headers = {"User-Agent": "Mozilla/5.0", "Accept": "application/pdf"}

    r = requests.get(url, headers=headers)

    # Load the PDF content into PyMuPDF from memory
    pdf_file = fitz.open(stream=io.BytesIO(r.content), filetype="pdf")

    # Extract text from each page
    full_text = ""
    for page in pdf_file:
        full_text += page.get_text()
    return full_text



