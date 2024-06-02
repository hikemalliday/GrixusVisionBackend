from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from config import ORIGINS
from logic import get_items
app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], 
    allow_credentials=True, 
    allow_methods=["*"],  
    allow_headers=["*"],  
)

@app.get("/get_items")
async def root():
    return get_items()