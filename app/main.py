import io
from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware
from sample import data

app = FastAPI()

@app.get("/")
def root():
    return {"message": "Welcome to 2B Model"}

@app.get("/get-file")
def analyseFile():
    return data[0]
