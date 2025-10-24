from dotenv import load_dotenv
import os
import requests
import pandas as pd
import pygsheets
import time
import asyncio
from fastapi import FastAPI,Request
import methods

app = FastAPI()

# Example methods

@app.get("/")
async def root():
    return {"message": "Hello World"}

@app.get("/test/")
def test_call():

    methods.get_puuid()

    return {"poggers": "test"}
