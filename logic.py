import os
import sqlite3
from datetime import timedelta, datetime
from fastapi import HTTPException
from starlette import status
from passlib.context import CryptContext
from fastapi.security import OAuth2PasswordBearer
from jose import jwt
from config import SECRET_ACCESS_KEY, SECRET_REFRESH_KEY, ALGORITHM, DB_DIR, LOCAL_DB

bcrypt_context = CryptContext(schemes=['bcrypt'], deprecated='auto')
oauth2_bearer = OAuth2PasswordBearer(tokenUrl='/token')

def get_newest_db(DB_DIR):
    if DB_DIR == LOCAL_DB:
        return DB_DIR + "master.db"
    
    newest_file = None
    newest_time = 0

    for file in os.listdir(DB_DIR):
        file_path = os.path.join(DB_DIR, file)
        if os.path.isfile(file_path):
            creation_time = os.path.getctime(file_path)
            if creation_time > newest_time:
                newest_time = creation_time
                newest_file = file_path  
    return newest_file

def get_items_wrapper(page: int, limit: int, char_name: str, item_name: str):
    count = get_items(page, limit, char_name, item_name, False)
    results = get_items(page, limit, char_name, item_name, True)
    results["count"] = count
    return results

def get_items(page: int, limit: int, char_name: str, item_name: str, paginate: bool):
    DB_FILE = get_newest_db(DB_DIR)
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    offset = (page - 1) * limit 

    try:
        if paginate:
            query = '''SELECT * FROM char_inventory'''
        else:
            query = '''SELECT COUNT(*) FROM char_inventory'''
        params = []
        
        if char_name and item_name:
            query += ' WHERE char_name = ? AND item_name LIKE ?'
            params.extend([char_name, f"%{item_name}%"])
        elif char_name:
            query += ' WHERE char_name = ?'
            params.append(char_name)
        elif item_name:
            query += ' WHERE item_name LIKE ?'
            params.append(f"%{item_name}%")

        if paginate:
            query += ' LIMIT ? OFFSET ?'
            params.extend([limit, offset])
        
        cursor.execute(query, tuple(params))
        results = cursor.fetchall()
        if paginate:
            new_results = [
                {
                    "charName": result[1],
                    "charGuild": result[2],
                    "itemName": result[3],
                    "itemCount": result[4],
                    "itemLocation": result[5]
                } for result in results
            ]
            return {
                "items": new_results,
                "dbFile": DB_FILE
            }
        else:
            count = results[0][0]
            return count
    
        
    except Exception as e:
        print(e)
        return {
            "items": [],
            "dbFile": ""
        }
    finally:
        conn.close()

def create_user(request):
    username = request.username
    password = request.password
    hashed_password = bcrypt_context.hash(password)
    query = '''INSERT INTO Users (username, hashed_password) VALUES (?, ?)'''
    try:
        conn = sqlite3.connect("./data/auth.db")
        cursor = conn.cursor()
        cursor.execute(query, (username, hashed_password))
        conn.commit()
        return {"message": "User created", "username": username}
    except Exception as e:
        print(e)
        return {"message": "Create user failed"}
    finally:
        conn.close()

def authenticate_user(username: str, password: str):
    try:
        conn = sqlite3.connect("./data/auth.db")
        cursor = conn.cursor()
        query = '''SELECT * FROM Users WHERE username = ?'''
        cursor.execute(query, (username,))
        user = cursor.fetchone()
        if user:
            id, username, hashed_password, resfresh_token = user
        else:
            return False
        if not bcrypt_context.verify(password, hashed_password):
            return False

        user_dict = {"id": id, "username": username, "hashed_password": hashed_password}
        return user_dict
    except Exception as e:
        print(e)
        return False
    finally:
        conn.close()

def create_access_token(username: str, user_id: int, expires_delta: timedelta):
    encode = {"username": username, "id": user_id}
    expires = datetime.utcnow() + expires_delta
    encode.update({"exp": expires})
    return jwt.encode(encode, SECRET_ACCESS_KEY, algorithm=ALGORITHM)

def create_refresh_token(username: str, user_id: int, expires_delta: timedelta):
    encode = {"username": username, "id": user_id}
    expires = datetime.utcnow() + expires_delta
    encode.update({"exp": expires})
    return jwt.encode(encode, SECRET_REFRESH_KEY, algorithm=ALGORITHM)

def handle_insert_refresh_token(username: str, id: str, refresh_token):
    try:
        conn = sqlite3.connect("./data/auth.db")
        cursor = conn.cursor()
        clear_query = '''UPDATE Users SET refresh_token = NULL WHERE username = ? AND id = ?'''
        cursor.execute(clear_query, (username, id))
        conn.commit()
        print("Refresh token cleared (set to null).")

        insert_query = '''UPDATE Users SET refresh_token = ? WHERE username = ? and id = ?'''
        cursor.execute(insert_query, (refresh_token, username, id))
        conn.commit()
        return True
    except sqlite3.Error as e:
        print(f"sqlite exception: {e}")
        return False
    except Exception as e:
        print(f"General exception: {e}")
        return False
    finally:
        conn.close()


def handle_login(username: str, password: str):
    user = authenticate_user(username, password)
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED,
                            detail="Could not validate user.")
    access_token = create_access_token(user["username"], user["id"], timedelta(minutes=30))
    refresh_token = create_refresh_token(user["username"], user["id"], timedelta(minutes=60))
    token_is_inserted = handle_insert_refresh_token(username, user["id"], refresh_token)

    if not token_is_inserted:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Could not insert refresh token.",
        )
    
    return {"access_token": access_token, "token_type": "bearer", "refresh_token": refresh_token}

def handle_refresh(token: str):
    try:
        payload = jwt.decode(token, SECRET_REFRESH_KEY, algorithms=[ALGORITHM])
        access_token = create_access_token(payload.get("username"), payload.get("id"), timedelta(minutes=30))
        return {"access_token": access_token}
    except Exception as e:
        print(e)
        return e
    
def get_char_names():
    try:
        DB_FILE = get_newest_db(DB_DIR)
        conn = sqlite3.connect(DB_FILE)
        cursor = conn.cursor()
        query = '''SELECT DISTINCT char_name FROM char_inventory'''
        cursor.execute(query)
        return [char_name[0] for char_name in cursor.fetchall()]
    except Exception as e:
        print(e)
        return e
    finally:
        conn.close()


    