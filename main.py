from dotenv import load_dotenv
import os
import requests
import pandas as pd
import pygsheets
import time
from fastapi import FastAPI, Request
import methods

app = FastAPI()

@app.get("/")
async def root():
    return {"message": "Hello World"}

@app.on_event("startup")
async def startup_event():
    methods.run_data_fetch_and_upload()

@app.get("/test/")
async def test_call():
    methods.run_data_fetch_and_upload()  
    
    return {"poggers": "test"}