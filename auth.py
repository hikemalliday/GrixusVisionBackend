from datetime import timedelta, datetime
from typing import Annotated
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from starlette import status
from passlib.context import CryptContext
from fastapi.security import OAuth2PasswordRequestForm, OAuth2PasswordBearer
from jose import jwt, JWTError
from config import SECRET_KEY, ALOGRITHM

# Interesting what the tutorial does here:
# Wonder if same approach could be used for sqlite
# def get_db():
#     db = SessionLocal()
#     try:
#         yield db
#     finally:
#         db.close()

# Not sure what this is for:


# db_dependency = Annotated[Session, Depends(get_db)]

# @router.post("/", status_code=status.HTTP_201_CREATED)
# async def create_user(db: db_dependency,
#                       create_user_request: CreateUserRequest):
#     create_user_model = Users(
#         username=create_user_request.username,
#         # This line passes in the password string and creates a hash
#         hashed_password=bcrypt_context.hash(create_user_request.password),
#     )

#     db.add(create_user_model)
#     db.commit()

# This function inserts the username and password