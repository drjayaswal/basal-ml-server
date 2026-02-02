import re
import os
import io
import nltk
import httpx

nltk_data_path = os.path.join(os.getcwd(), "nltk_data")
nltk.data.path.append(nltk_data_path)
nltk.download('punkt')
nltk.download('punkt_tab')

from docx import Document
from PyPDF2 import PdfReader
from nltk.tokenize import word_tokenize
from nltk.stem import WordNetLemmatizer
from nltk.corpus import stopwords, wordnet
from app.libs.const import CORPORATE_NOISE_TAXONOMY, DAYS, MONTHS


def text(content: bytes, mime_type: str) -> str:
    text = ""
    try:
        if not content: return ""
        stream = io.BytesIO(content)
        if "pdf" in mime_type:
            reader = PdfReader(stream)
            text = " ".join([p.extract_text() for p in reader.pages if p.extract_text()])
        elif "wordprocessingml" in mime_type or mime_type.endswith("docx"):
            doc = Document(stream)
            text = " ".join([para.text for para in doc.paragraphs if para.text])
        else:
            text = content.decode("utf-8", errors="ignore")
    except Exception as e:
        raise Exception({"message":f"Extraction Error: {str(e)}"})
    return text.strip()

async def text_from_url(url: str):
    async with httpx.AsyncClient(follow_redirects=True, timeout=60.0) as client:
        resp = await client.get(url)
        if resp.status_code != 200:
            raise Exception(f"Download Error: {resp.status_code}")
        m_type = resp.headers.get("Content-Type", "").lower()
        if not m_type or "octet-stream" in m_type:
            ext = url.split('?')[0].lower()
            if ext.endswith(".pdf"): m_type = "application/pdf"
            elif ext.endswith(".docx"): m_type = "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
            else: m_type = "text/plain"
        return text(content=resp.content, mime_type=m_type)

def get_info(text):
    emails = list(set(re.findall(r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}', text)))
    phones = list(set(re.findall(r'\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}', text)))
    links = list(set(re.findall(r'(https?://(?:www\.)?(?:linkedin\.com|github\.com|behance\.net)\S*)', text)))
    return {"contact": {"emails": emails, "phones": phones, "links": links}}

def get_wordnet_pos(tag):
    if tag.startswith('J'): return wordnet.ADJ
    elif tag.startswith('V'): return wordnet.VERB
    elif tag.startswith('R'): return wordnet.ADV
    else: return wordnet.NOUN

def lemmatize_text(text):
    stop_words = set(stopwords.words('english'))
    text = re.sub(r'[^a-zA-Z0-9+#.\s]', ' ', text.lower())
    tokens = word_tokenize(text)
    tagged_tokens = nltk.pos_tag(tokens)
    lemmatizer = WordNetLemmatizer()
    lemmatized = []
    for word, tag in tagged_tokens:
        if word not in stop_words:
            lemma = lemmatizer.lemmatize(word, get_wordnet_pos(tag))
            lemmatized.append((lemma, tag))
    return lemmatized

def filter_noise(text):
    tagged_tuples = lemmatize_text(text=text)
    CORPORATE_STOPLIST = {word.lower() for sublist in CORPORATE_NOISE_TAXONOMY.values() for word in sublist}
    skills, noise = set(), set()
    valid_tags = ['NN', 'NNS', 'NNP', 'JJ']
    stop_set = set(stopwords.words('english'))
    for word, tag in tagged_tuples:
        clean_word = word.lower()
        if tag in valid_tags:
            if clean_word in CORPORATE_STOPLIST or clean_word in MONTHS or clean_word in DAYS or clean_word in stop_set:
                noise.add(clean_word)
            else:
                skills.add(clean_word)
        else:
            noise.add(clean_word)
    return sorted(list(skills)), sorted(list(noise))
