import boto3
import httpx
from app.config import settings
from urllib.parse import urlparse
from botocore.config import Config
from app.services.process import process
from fastapi import FastAPI, HTTPException
from app.services.extract import extext, extract_text_from_url

get_settings = settings()
app = FastAPI()

s3_client = boto3.client(
    's3',
    aws_access_key_id=get_settings.AWS_ACCESS_KEY,
    aws_secret_access_key=get_settings.AWS_SECRET_ACCESS_KEY,
    region_name=get_settings.AWS_REGION,
    config=Config(
        signature_version='s3v4',
        retries={'max_attempts': 5},
        s3={'addressing_style': 'virtual'}
    )
)

@app.post("/analyze-s3")
async def analyze_s3(data: dict):
    file_url = data.get('file_url')
    description = data.get('description')
    filename = data.get('filename', 's3_file')

    if not file_url or not description:
        raise HTTPException(status_code=400, detail="Missing file_url or description")

    try:
        resume_text = await extext(file_url)
        
        results = await process(resume_text, description, filename)

        try:
            parsed_url = urlparse(file_url)
            host_parts = parsed_url.netloc.split('.')
            
            if host_parts[0] == 's3':
                path_parts = parsed_url.path.lstrip('/').split('/')
                bucket_name = path_parts[0]
                s3_key = "/".join(path_parts[1:])
            else:
                bucket_name = host_parts[0]
                s3_key = parsed_url.path.lstrip('/')
            
            s3_key = s3_key.split('?')[0]
            
            s3_client.delete_object(Bucket=bucket_name, Key=s3_key)
            print(f"Cleanup Success: Deleted {s3_key} from {bucket_name}")
        except Exception as delete_err:
            print(f"Cleanup Failed (Non-critical): {delete_err}")

        return results

    except Exception as e:
        print(f"S3 Route Error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/analyze-drive")
async def analyze_drive(data: dict):
    file_id = data.get("file_id")
    token = data.get("google_token")
    description = data.get("description", "")
    filename = data.get("filename", "drive_file")
    mime_type = data.get("mime_type", "")

    if not file_id or not token:
        raise HTTPException(status_code=400, detail="Missing credentials")

    try:
        async with httpx.AsyncClient(follow_redirects=True) as client:
            if "google-apps" in mime_type:
                url = f"https://www.googleapis.com/drive/v3/files/{file_id}/export?mimeType=application/pdf"
                target_mime = "application/pdf"
            else:
                url = f"https://www.googleapis.com/drive/v3/files/{file_id}?alt=media"
                target_mime = mime_type

            resp = await client.get(url, headers={"Authorization": f"Bearer {token}"}, timeout=45.0)

            if resp.status_code != 200:
                raise Exception(f"Google Drive Error {resp.status_code}: {resp.text[:100]}")

            if len(resp.content) < 200:
                 raise Exception("File content too small; likely a failed download.")

            resume_text = extract_text_from_url(resp.content, target_mime)

        return await process(resume_text, description, filename)

    except Exception as e:
        print(f"Drive Logic Crash: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))