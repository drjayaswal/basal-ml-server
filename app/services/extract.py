import io
import httpx
from PyPDF2 import PdfReader
from docx import Document

def extract_text_from_url(content: bytes, mime_type: str) -> str:
    """Extracts text from binary content based on mime_type."""
    text = ""
    try:
        if not content:
            return ""

        if mime_type == "application/pdf":
            stream = io.BytesIO(content)
            reader = PdfReader(stream)
            page_texts = [page.extract_text() for page in reader.pages if page.extract_text()]
            text = " ".join(page_texts)

        elif mime_type == "application/vnd.openxmlformats-officedocument.wordprocessingml.document":
            stream = io.BytesIO(content)
            doc = Document(stream)
            text = " ".join([para.text for para in doc.paragraphs if para.text])

        elif mime_type == "text/plain":
            text = content.decode("utf-8", errors="ignore")

    except Exception as e:
        print(f"Extraction Error: {str(e)}")
        
    return text.strip()

async def extext(url: str):
    """Downloads content from URL and detects mime_type automatically."""
    async with httpx.AsyncClient(follow_redirects=True, timeout=30.0) as client:
        resp = await client.get(url)
        if resp.status_code != 200:
            raise Exception(f"Download Error: {resp.status_code}")
        
        ext = url.split('?')[0].lower()
        if ext.endswith(".pdf"): 
            m_type = "application/pdf"
        elif ext.endswith(".docx"): 
            m_type = "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
        else: 
            m_type = "text/plain"

        return extract_text_from_url(content=resp.content, mime_type=m_type)