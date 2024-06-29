from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from config import ORIGINS
from logic import handle_login, get_items, create_user, handle_refresh
from typing import Annotated
from auth_table import create_table, user_table
from fastapi.security import OAuth2PasswordRequestForm, OAuth2PasswordBearer
from fastapi.responses import JSONResponse
import logging
from auth_handler import AuthHandler

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

create_table(user_table)

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
                   "http://localhost:3000",
                   "http://45.55.129.24:3000", 
                   "http://45.55.129.24:3000/home", 
                   "http://127.0.0.1:5173", 
                   "http://127.0.0.1:5174", 
                   "http://127.0.0.1:5173/home"
                   ], 
    allow_credentials=True, 
    allow_methods=["*"],  
    allow_headers=["*"],  
)


app.add_middleware(AuthHandler)

class CreateUserRequest(BaseModel):
    username: str
    password: str

class Token(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str

class Refresh(BaseModel):
    refresh_token: str

@app.exception_handler(Exception)
async def global_exception_handler(_, exc):
    logger.error(f"Unhandled error: {exc}")
    return JSONResponse(
        status_code=500,
        content={"message": "Internal Server Error"},
    )

@app.get("/get_items")
async def get_items_endpoint():
    try:
        return get_items()
    except Exception as e:
        print(e)

@app.post("/create_user")
async def create_user_endpoint(request: CreateUserRequest):
    try:
        return create_user(request)
    
    except Exception as e:
        print(e)
        return {"message": "Error creating user"}
    
@app.post("/login", response_model=Token)
async def login_for_access_token(form_data: Annotated[OAuth2PasswordRequestForm, Depends()]):
    try:
        return handle_login(form_data.username, form_data.password)
    except Exception as e:
        print(e)
        return {"message": "failed to log in."}

# @app.get("/refresh")
# async def refresh(request: Request):
#     print(request.cookies)
#     # Basically, we need to take in the refresh token + username, and search the database for that user
#     # We then check to see if our refresh token matches the refresh token in the db
#     # This is why tokens must be created with the username
#     return {"message": "/refresh endpoint test"}

@app.post("/refresh")
async def refresh(request: Refresh):
    print(request.refresh_token)
    return handle_refresh(request.refresh_token)

@app.on_event("shutdown")
async def shutdown_event():
    logger.info("Shutting down...")