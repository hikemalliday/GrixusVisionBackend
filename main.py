from fastapi import FastAPI, Depends, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi_pagination import Page, Params
from fastapi.security import OAuth2PasswordRequestForm
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from logic import handle_login, get_items_wrapper, create_user, handle_refresh, get_char_names
from typing import Annotated
from auth_table import create_table, user_table
from auth_handler import AuthHandler
import logging
from typing import Optional, List, TypeVar, Generic
# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

create_table(user_table)

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
                   "http://localhost:5173",
                   "http://localhost:3000",
                   "0.0.0.0:3000", 
                   "0.0.0.0:3000/home", 
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

class Item(BaseModel):
    itemName: str
    charName: str
    itemCount: int
    itemLocation: str
    charGuild: str

class ItemResponse(BaseModel):
    results: List[Item]
    dbFile: str
    page: int
    size: int
    count: int

class CharNames(BaseModel):
    charName: str

T = TypeVar("T")

class CustomPage(Page[T], Generic[T]):
    custom_property: str


def custom_paginate(object: dict, page: int, size: int) -> ItemResponse:
    return {
        "results": object["items"],
        "dbFile": object["dbFile"],
        "count": object["count"],
        "page": page,
        "size": size,
    }


@app.exception_handler(Exception)
async def global_exception_handler(_, exc):
    logger.error(f"Unhandled error: {exc}")
    return JSONResponse(
        status_code=500,
        content={"message": "Internal Server Error"},
    )

@app.get("/get_items", response_model=ItemResponse)
async def get_items_endpoint(
    params: Params = Depends(),  
    char_name: Optional[str] = Query("", alias="charName"),
    item_name: Optional[str] = Query("", alias="itemName")
    ):
    try:
        if char_name == "ALL":
            char_name = ""
        page = params.page
        limit = params.size
        items_query_object = get_items_wrapper(page, limit, char_name, item_name)
        custom_results = custom_paginate(items_query_object, page, limit)
        return custom_results
    except Exception as e:
        print(e)

@app.get("/get_char_names")
async def get_char_names_endpoint():
    try:
        char_names = get_char_names()
        return char_names
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

@app.post("/refresh")
async def refresh(request: Refresh):
    return handle_refresh(request.refresh_token)

@app.on_event("shutdown")
async def shutdown_event():
    logger.info("Shutting down...")