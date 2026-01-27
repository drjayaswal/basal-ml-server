import re
from sklearn.metrics.pairwise import cosine_similarity
from sklearn.feature_extraction.text import TfidfVectorizer

async def process(resume_text: str, description: str, filename: str):
    try:
        if not resume_text or len(resume_text.strip()) < 20:
            raise ValueError("Insufficient text extracted.")

        texts = [resume_text.lower(), description.lower()]
        vectorizer = TfidfVectorizer(stop_words='english')
        tfidf_matrix = vectorizer.fit_transform(texts)
        similarity_score = cosine_similarity(tfidf_matrix[0:1], tfidf_matrix[1:2])[0][0]

        def get_words(text):
            return set(re.findall(r'\b\w{3,}\b', text.lower()))

        resume_words = get_words(resume_text)
        desc_words = get_words(description)
        
        matched_keywords = sorted(list(resume_words.intersection(desc_words)))
        missing_keywords = sorted(list(desc_words.difference(resume_words)))

        return {
            "status": "success",
            "filename": filename,
            "match_score": round(float(similarity_score) * 100, 2),
            "analysis_details": {
                "matched_keywords": matched_keywords[:15],
                "missing_keywords": missing_keywords[:15],
                "total_matches": len(matched_keywords),
                "total_lags": len(missing_keywords),
                "summary": f"Analyzed {filename}."
            }
        }
    except Exception as e:
        return {
            "status": "failed",
            "filename": filename,
            "match_score": 0,
            "analysis_details": {"summary": f"Error: {str(e)}", "matched_keywords": [], "missing_keywords": []}
        }