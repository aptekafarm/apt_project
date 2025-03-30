import sqlite3

DATABASE = "sales.db"

def get_db_connection():
    """ Маълумотлар базасига уланишни таъминлайди """
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row  # JSON formatda natija qaytarish uchun
    return conn

def init_db():
    """ Маълумотлар базасини яратиш ёки янгилаш """
    conn = get_db_connection()
    cursor = conn.cursor()

    # ✅ Кунлик савдо жадвали
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS sales (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            sana TEXT NOT NULL,
            inkassa REAL DEFAULT 0,
            terminal_term REAL DEFAULT 0,
            terminal_humo REAL DEFAULT 0,
            nakd REAL DEFAULT 0,
            jami_tushum REAL DEFAULT 0
        )
    """)

    # ✅ Чиқимлар жадвали
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS expenses (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            sana TEXT NOT NULL,
            xarajat_nomi TEXT NOT NULL,
            miqdor REAL DEFAULT 0,
            izoh TEXT
        )
    """)

    # ✅ Товар кирими жадвали
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS product_income (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            sana TEXT NOT NULL,
            yetkazib_beruvchi TEXT NOT NULL,
            summa_prixod REAL NOT NULL,
            summa_roznichn REAL DEFAULT 0,
            perechesleniya REAL DEFAULT 0,
            nakd_pul REAL DEFAULT 0,
            qarz REAL NOT NULL
        )
    """)

    # ✅ Hisobot жадвали
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS hisobot (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            sana TEXT NOT NULL,
            jami_savdo REAL DEFAULT 0,
            jami_tovar_kirimi REAL DEFAULT 0,
            jami_harajatlar REAL DEFAULT 0,
            tovar_qoldigi_boshida REAL DEFAULT 0,
            tovar_qoldigi_oxirida REAL DEFAULT 0
        )
    """)

    # ✅ Фойдаланувчилар жадвали
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL,
            role TEXT DEFAULT 'employee'  -- 'admin' ёки 'employee'
        )
    """)

    # ✅ Онлайн фойдаланувчилар жадвали
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users_online (
            user_id INTEGER,
            username TEXT,
            last_active TIMESTAMP
        )
    """)

    # ✅ Аудит лог (тарих) жадвали
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS audit_log (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            username TEXT,
            action TEXT,
            table_name TEXT,
            record_id INTEGER,
            timestamp TEXT,
            details TEXT
        )
    """)

    conn.commit()
    conn.close()
    print("✅ Ма'lumotлар базаси яратилди ва янгиланди!")


def log_action(user_id, username, action, table_name, record_id=None, details=None):
    conn = get_db_connection()
    conn.execute("""
        INSERT INTO audit_log (user_id, username, action, table_name, record_id, timestamp, details)
        VALUES (?, ?, ?, ?, ?, datetime('now'), ?)
    """, (user_id, username, action, table_name, record_id, details))
    conn.commit()
    conn.close()

if __name__ == "__main__":
    init_db()
