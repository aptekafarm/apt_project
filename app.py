import sqlite3
from flask import Flask
from routes import bp as routes_bp
from dotenv import load_dotenv
import os
from werkzeug.security import generate_password_hash  # ✅ Паролни хэшлаш учун импорт
from flask import session
from datetime import datetime
from flask import g


app = Flask(__name__)
load_dotenv()
app.secret_key = os.getenv("SECRET_KEY")  # ✅ .env файлдан махфий калит олинади

# 🔐 Session учун қўлланиладиган калит
# app.secret_key = "bu_juda_maxfiy_kalit_123"  # Агар .env ишламаса, ушбу қаторни ишлатинг

app.register_blueprint(routes_bp)

# 📂 Маълумотлар базаси номи
DATABASE = "sales.db"

def get_db_connection():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row  # JSON форматда қайтариш учун
    return conn

def init_db():
    """🛠 Bazani yaratish funksiyasi"""
    with get_db_connection() as conn:
        cursor = conn.cursor()

        # 🧾 Savdolar жадвали
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS sales (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                sana TEXT,
                inkassa REAL,
                terminal_term REAL,
                terminal_humo REAL,
                nakd REAL,
                jami_tushum REAL
            )
        """)

        # 💸 Харажатлар жадвали
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS expenses (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                sana TEXT,
                xarajat_nomi TEXT,
                miqdor REAL,
                izoh TEXT
            )
        """)

        # 👥 Фойдаланувчилар жадвали
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE NOT NULL,
                password TEXT NOT NULL,
                role TEXT DEFAULT 'user'
            )
        """)

        # ✅ Агар 'admin' йўқ бўлса — қўшамиз:
        cursor.execute("SELECT COUNT(*) FROM users WHERE username = 'admin'")
        if cursor.fetchone()[0] == 0:
            hashed_admin_pass = generate_password_hash("admin123")  # 🔒 Парол хэшланади
            cursor.execute("INSERT INTO users (username, password, role) VALUES (?, ?, ?)",
                           ("admin", hashed_admin_pass, "admin"))

        conn.commit()
    conn.close()

@app.before_request
def update_user_activity():
    if "user_id" in session and "username" in session:
        conn = get_db_connection()
        conn.execute("""
            INSERT OR REPLACE INTO users_online (user_id, username, last_active)
            VALUES (?, ?, ?)
        """, (session["user_id"], session["username"], datetime.now()))
        conn.commit()
        conn.close()


@app.before_request
def update_user_online():
    if "user_id" in session:
        conn = get_db_connection()
        conn.execute("""
            INSERT OR REPLACE INTO users_online (user_id, username, last_active)
            VALUES (?, ?, ?)
        """, (session["user_id"], session["username"], datetime.now()))
        conn.commit()
        conn.close()


# ✅ Дастлабки базани тайёрлаймиз
init_db()

# 🚀 Серверни ишга тушурамиз
if __name__ == "__main__":
    app.run(debug=True)
