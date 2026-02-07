from pydantic import BaseModel

class AnalysisRequest(BaseModel):
    file_url: str
    filename: str
    description: str