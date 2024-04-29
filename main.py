from fastapi import FastAPI, Request, Form, HTTPException
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
import sqlite3

app = FastAPI()
templates = Jinja2Templates(directory="templates")

try:
    conn = sqlite3.connect("test.db")
    cursor = conn.cursor()
except sqlite3.Error as e:
    print("Ошибка при подключении к базе данных SQLite:", e)

def drop_table():
    try:
        cursor.execute("DROP TABLE IF EXISTS user_info")
        conn.commit()
    except sqlite3.Error as e:
        print("Ошибка при удалении таблицы пользователей:", e)

def reset_sequence():
    try:
        cursor.execute("DELETE FROM sqlite_sequence WHERE name='user_info'")
        conn.commit()
    except sqlite3.Error as e:
        print("Ошибка при сбросе последовательности:", e)

reset_sequence()
drop_table()

def create_table():
    try:
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS user_info (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            login TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL,
            height REAL,
            age INTEGER,
            name TEXT
        )
        """)
        conn.commit()
    except sqlite3.Error as e:
        print("Ошибка при создании таблицы пользователей:", e)

create_table()

@app.get("/", response_class=HTMLResponse)
async def read_root(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

@app.get("/sign_up", response_class=HTMLResponse)
async def sign_up_form(request: Request):
    return templates.TemplateResponse("sign_up.html", {"request": request})

@app.post("/sign_up", response_class=HTMLResponse)
async def sign_up(request: Request, login: str = Form(...), password: str = Form(...), height: float = Form(...), age: int = Form(...), name: str = Form(...)):
    try:
        cursor.execute("""
        INSERT INTO user_info (login, password, height, age, name) VALUES (?, ?, ?, ?, ?)
        """, (login, password, height, age, name))
        conn.commit()
        reset_sequence()
        user_info = fetch_user(login)
        print("User Info:", user_info)
        if user_info:
            return templates.TemplateResponse("user_info.html", {"request": request, "user_info": user_info})
        else:
            raise HTTPException(status_code=404, detail="Пользователь не найден")
    except sqlite3.Error as e:
        print("Ошибка при регистрации пользователя:", e)
        raise HTTPException(status_code=500, detail="Внутренняя ошибка сервера")

@app.get("/sign_in", response_class=HTMLResponse)
async def sign_in_form(request: Request):
    return templates.TemplateResponse("sign_in.html", {"request": request})

@app.post("/sign_in", response_class=HTMLResponse)
async def sign_in(request: Request, login: str = Form(...), password: str = Form(...)):
    try:
        user_info = fetch_user(login)
        if user_info and user_info[2] == password:
            return templates.TemplateResponse("user_info.html", {"request": request, "user_info": user_info})
        else:
            return templates.TemplateResponse("login_failed.html", {"request": request})
    except sqlite3.Error as e:
        print("Ошибка при входе пользователя:", e)
        raise HTTPException(status_code=500, detail="Внутренняя ошибка сервера")

def fetch_user(login):
    try:
        cursor.execute("SELECT * FROM user_info WHERE login = ?", (login,))
        return cursor.fetchone()
    except sqlite3.Error as e:
        print("Ошибка при получении информации о пользователе:", e)
        raise HTTPException(status_code=500, detail="Внутренняя ошибка сервера")
