from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse

from jose import jwt
from config import SECRET_ACCESS_KEY, ALGORITHM

class AuthHandler(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        if request.method == "OPTIONS":
            return await call_next(request)
        if request.url.path not in [
            "/token", 
            "/docs", 
            "/openapi.json", 
            "/create_user", 
            "/login/", 
            "/login", 
            "/refresh", 
            "/refresh/"
            ]:
            token = request.headers.get("authorization")
            if token is None or not token.startswith("Bearer "):
                return JSONResponse(status_code=401, content={"detail": "Not authenticated"})
            
            token = token[len("Bearer "):]
            try:
                # This line checks for validity of Access Token
                payload = jwt.decode(token, SECRET_ACCESS_KEY, algorithms=[ALGORITHM])
                request.state.user = {"username": payload.get("username"), "id": payload.get("id")}
            except Exception:
                print("auth handler could not validate")
                return JSONResponse(status_code=401, content={"detail": "Could not validate token"})

        response = await call_next(request)
        return response
    
    