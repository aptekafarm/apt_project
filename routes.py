from flask import Blueprint, render_template, request, redirect, url_for, session, flash
from database import get_db_connection
from datetime import datetime
from functools import wraps
from werkzeug.security import generate_password_hash, check_password_hash
from database import log_action  # файл бошига
from flask import g


bp = Blueprint("routes", __name__)

# ✅ Login-required decorator
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if "user_id" not in session:
            return redirect(url_for("routes.login"))
        return f(*args, **kwargs)
    return decorated_function

# ✅ Admin-only decorator
def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if session.get("role") != "admin":
            flash("Фақат админ фойдаланувчига рухсат берилган!", "danger")
            return redirect(url_for("routes.index"))
        return f(*args, **kwargs)
    return decorated_function

# ✅ Raqamlarni minlik форматда чиқариш
def format_number(value):
    try:
        return "{:,.2f}".format(float(value)).replace(",", " ")
    except (ValueError, TypeError):
        return value

# ✅ Кунлик савдо рўйхати
@bp.route("/")
@login_required
def index():
    conn = get_db_connection()
    sales = conn.execute("SELECT * FROM sales").fetchall()

    # ✅ Жами тушумни ҳисоблаш
    total_inkassa = sum(float(row["inkassa"]) for row in sales)
    total_terminal_term = sum(float(row["terminal_term"]) for row in sales)
    total_terminal_humo = sum(float(row["terminal_humo"]) for row in sales)
    total_nakd = sum(float(row["nakd"]) for row in sales)
    total_jami_tushum = sum(float(row["jami_tushum"]) for row in sales)

    conn.close()
    return render_template(
        "index.html", 
        sales=sales,
        total_inkassa=format_number(total_inkassa),
        total_terminal_term=format_number(total_terminal_term),
        total_terminal_humo=format_number(total_terminal_humo),
        total_nakd=format_number(total_nakd),
        total_jami_tushum=format_number(total_jami_tushum)
    )

# ✅ Янги савдони қўшиш
@bp.route("/add", methods=["POST"])
@login_required
def add_sale():
    try:
        sana = request.form["sana"]
        inkassa = float(request.form.get("inkassa", 0))
        terminal_term = float(request.form.get("terminal_term", 0))
        terminal_humo = float(request.form.get("terminal_humo", 0))
        nakd = float(request.form.get("nakd", 0))
        jami_tushum = inkassa + terminal_term + terminal_humo + nakd

        conn = get_db_connection()
        conn.execute(
            "INSERT INTO sales (sana, inkassa, terminal_term, terminal_humo, nakd, jami_tushum) VALUES (?, ?, ?, ?, ?, ?)",
            (sana, inkassa, terminal_term, terminal_humo, nakd, jami_tushum)
        )
        conn.commit()
        conn.close()
                # ✅ Аудит логга ёзиш
        log_action(session["user_id"], session["username"], "Qo‘shish", "sales", details=details)

        return redirect(url_for("routes.index"))

    except Exception as e:
        return f"Xatolik yuz berdi: {str(e)}"

# ✅ Савдони таҳрирлаш
@bp.route("/edit_sales/<int:id>", methods=["GET", "POST"])
@login_required
@admin_required
def edit_sales(id):
    conn = get_db_connection()
    old_data = conn.execute("SELECT * FROM sales WHERE id = ?", (id,)).fetchone()
    sale = conn.execute("SELECT * FROM sales WHERE id = ?", (id,)).fetchone()

    if sale is None:
        return "Маълумот топилмади", 404

    if request.method == "POST":
        sana = request.form["sana"]
        inkassa = float(request.form.get("inkassa", 0))
        terminal_term = float(request.form.get("terminal_term", 0))
        terminal_humo = float(request.form.get("terminal_humo", 0))
        nakd = float(request.form.get("nakd", 0))
        jami_tushum = inkassa + terminal_term + terminal_humo + nakd

        # ✅ Шу ерда details ни шакллантирамиз
        details = (
            f"Эски сумма: {old_data['jami_tushum']}, "
            f"Эски сана: {old_data['sana']}, "
            f"Янги сумма: {jami_tushum}, "
            f"Янги сана: {sana}"
        )

        # ✅ Шу ерда маълумотни янгилаймиз
        conn.execute(
            "UPDATE sales SET sana = ?, inkassa = ?, terminal_term = ?, terminal_humo = ?, nakd = ?, jami_tushum = ? WHERE id = ?",
            (sana, inkassa, terminal_term, terminal_humo, nakd, jami_tushum, id)
        )
        conn.commit()

        # ✅ Аудит лог ёзувини киритамиз
        log_action(
            session["user_id"],
            session["username"],
            "Таҳрирланди",
            "sales",
            record_id=id,
            details=details
        )

        conn.close()
        return redirect(url_for("routes.index"))

    conn.close()
    return render_template("edit_sales.html", sale=sale)


@bp.route("/expenses")
@login_required
def expenses():
    conn = get_db_connection()
    expenses_list = conn.execute("SELECT * FROM expenses").fetchall()

    total_miqdor = sum(float(row["miqdor"]) for row in expenses_list)

    conn.close()

    return render_template(
        "expenses.html",
        expenses=expenses_list,
        total_miqdor=format_number(total_miqdor),
        format_number=format_number  # ✅ format_number’ни HTML'га узатиш
    )


# ✅ Янги чиқим қўшиш
@bp.route("/add_expense", methods=["POST"])
@login_required
def add_expense():
    sana = request.form["sana"]
    xarajat_nomi = request.form["xarajat_nomi"]
    miqdor = float(request.form.get("miqdor", 0))
    izoh = request.form.get("izoh", "")

    conn = get_db_connection()
    conn.execute(
        "INSERT INTO expenses (sana, xarajat_nomi, miqdor, izoh) VALUES (?, ?, ?, ?)",
        (sana, xarajat_nomi, miqdor, izoh)
    )
    conn.commit()
    conn.close()
    
    log_action(session["user_id"], session["username"], "Qo‘шилди", "expenses", details=details)


    return redirect(url_for("routes.expenses"))


# ✅ Чиқимни таҳрирлаш
@bp.route("/edit_expenses/<int:id>", methods=["GET", "POST"])
def edit_expenses(id):
    conn = get_db_connection()
    expense = conn.execute("SELECT * FROM expenses WHERE id = ?", (id,)).fetchone()

    if expense is None:
        return "Маълумот топилмади", 404

    if request.method == "POST":
        sana = request.form["sana"]
        xarajat_nomi = request.form["xarajat_nomi"]
        miqdor = float(request.form.get("miqdor", 0))
        izoh = request.form.get("izoh")

        conn.execute(
            "UPDATE expenses SET sana = ?, xarajat_nomi = ?, miqdor = ?, izoh = ? WHERE id = ?",
            (sana, xarajat_nomi, miqdor, izoh, id)
        )
        conn.commit()
        log_action(session["user_id"], session["username"], "Таҳрирланди", "expenses", record_id=id, details=details)
        conn.close()
        return redirect(url_for("routes.expenses"))

    conn.close()
    return render_template("edit_expenses.html", expense=dict(expense))

# ✅ Товар кирими рўйхати
@bp.route("/product_income")
def product_income():
    conn = get_db_connection()
    income_list = conn.execute("SELECT * FROM product_income").fetchall()

    # ✅ SQLite объектини list(dict) га айлантириш
    income_list = [dict(row) for row in income_list]

    # ✅ Ҳар бир қатор учун Насенкани ҳисоблаш
    for row in income_list:
        row["natsenka"] = ((float(row["summa_roznichn"]) - float(row["summa_prixod"])) / float(row["summa_prixod"]) * 100) if float(row["summa_prixod"]) > 0 else 0

    # ✅ Умумий ҳисоб-китоблар
    total_summa_prixod = sum(float(row["summa_prixod"]) for row in income_list)
    total_summa_roznichn = sum(float(row["summa_roznichn"]) for row in income_list)
    total_perechesleniya = sum(float(row["perechesleniya"]) for row in income_list)
    total_nakd_pul = sum(float(row["nakd_pul"]) for row in income_list)
    total_qarz = sum(float(row["qarz"]) for row in income_list)

    # ✅ Умумий Насенка ҳисоблаш
    total_natsenka= ((total_summa_roznichn - total_summa_prixod) / total_summa_prixod * 100) if total_summa_prixod > 0 else 0

    conn.close()

    return render_template(
        "product_income.html", 
        income_list=income_list,
        total_summa_prixod=format_number(total_summa_prixod),
        total_summa_roznichn=format_number(total_summa_roznichn),
        total_natsenka=total_natsenka,  # ✅ Умумий наценка
        total_perechesleniya=format_number(total_perechesleniya),
        total_nakd_pul=format_number(total_nakd_pul),
        total_qarz=format_number(total_qarz),
        format_number=format_number
    )

# ✅ Янги товар киримини қўшиш
@bp.route("/add_product_income", methods=["POST"])
def add_product_income():
    try:
        # Forma ma'lumotlarini olish
        sana = request.form.get("sana", "").strip()
        yetkazib_beruvchi = request.form.get("yetkazib_beruvchi", "").strip()
        summa_prixod = request.form.get("summa_prixod", "0").replace(",", "").strip()
        summa_roznichn = request.form.get("summa_roznichn", "0").replace(",", "").strip()
        perechesleniya = request.form.get("perechesleniya", "0").replace(",", "").strip()
        nakd_pul = request.form.get("nakd_pul", "0").replace(",", "").strip()

        # Majburiy maydonlarni tekshirish
        if not sana or not yetkazib_beruvchi:
            return "❌ Хатолик: Сана ва етказиб берувчи маълумотлари тўлдирилиши шарт!"
        
         # Floatga o'tkazish
        try:
            summa_prixod = float(summa_prixod) if summa_prixod else 0
            summa_roznichn = float(summa_roznichn) if summa_roznichn else 0
            perechesleniya = float(perechesleniya) if perechesleniya else 0
            nakd_pul = float(nakd_pul) if nakd_pul else 0
        except ValueError:
            return "❌ Хатолик: Сумма киритишда рақамдан бошқа белги бўлмаслиги керак!"
        
        # Наценка ва қарзни ҳисоблаш
        natsenka = ((summa_roznichn - summa_prixod) / summa_prixod * 100) if summa_prixod > 0 else 0
        qarz = summa_prixod - perechesleniya - nakd_pul

         # Manfiy qiymatlar tekshiruvi
        if summa_prixod < 0 or summa_roznichn < 0 or perechesleniya < 0 or nakd_pul < 0 or qarz < 0:
            return "❌ Хатолик: Қийматлар манфий бўлмаслиги керак!"

        # Ma'lumotni bazaga kiritish
        conn = get_db_connection()
        conn.execute("""
            INSERT INTO product_income (sana, yetkazib_beruvchi, summa_prixod, summa_roznichn, natsenka, perechesleniya, nakd_pul, qarz)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (sana, yetkazib_beruvchi, summa_prixod, summa_roznichn, natsenka, perechesleniya, nakd_pul, qarz))

        conn.commit()
        conn.close()
        log_action(session["user_id"], session["username"], "Qo‘шилди", "product_income", details=details)

        return redirect(url_for("routes.product_income"))

    except Exception as e:
        return f"❌ Хатолик юз берди: {str(e)}"
          
@bp.route("/edit_product_income/<int:id>", methods=["GET", "POST"])
def edit_product_income(id):
    conn = get_db_connection()
    income = conn.execute("SELECT * FROM product_income WHERE id = ?", (id,)).fetchone()

    if income is None:
        return "Маълумот топилмади", 404

    if request.method == "POST":
        sana = request.form["sana"]
        yetkazib_beruvchi = request.form["yetkazib_beruvchi"]
        summa_prixod = float(request.form.get("summa_prixod", 0))
        summa_roznichn = float(request.form.get("summa_roznichn", 0))  # ✅ Янги майдон
        perechesleniya = float(request.form.get("perechesleniya", 0))
        nakd_pul = float(request.form.get("nakd_pul", 0))

        # Наценка фоизини ҳисоблаш
        if summa_prixod > 0:
            natsenka = ((summa_roznichn - summa_prixod) / summa_prixod) * 100
        else:
            natsenka = 0

        # Qarzni hisoblash
        qarz = summa_prixod - perechesleniya - nakd_pul  # ✅ Qarzni hisoblashni qo'shish

        # Ma'lumotlar bazasini yangilash
        conn.execute("""
            UPDATE product_income
            SET sana = ?, yetkazib_beruvchi = ?, summa_prixod = ?, summa_roznichn = ?, natsenka = ?, perechesleniya = ?, nakd_pul = ?, qarz = ?
            WHERE id = ?
        """, (sana, yetkazib_beruvchi, summa_prixod, summa_roznichn, natsenka, perechesleniya, nakd_pul, qarz, id))

        conn.commit()
        log_action(session["user_id"], session["username"], "Таҳрирланди", "product_income", record_id=id, details=details)
        conn.close()
        return redirect(url_for("routes.product_income"))

    conn.close()
    return render_template("edit_product_income.html", income=income)


@bp.route("/hisobotlar")
def hisobot_page():
    conn = get_db_connection()

    # Бир марта киритилган доимий сумма (бошланғич қолдиқ)
    initial_balance_row = conn.execute(
        "SELECT tovar_qoldigi_boshida FROM hisobot ORDER BY id ASC LIMIT 1"
    ).fetchone()
    tovar_qoldigi_boshida = (
        initial_balance_row["tovar_qoldigi_boshida"] if initial_balance_row else 0
    )

    # Барча кунлар учун умумий савдо
    sales_total = conn.execute(
        "SELECT SUM(jami_tushum) AS jami_savdo FROM sales"
    ).fetchone()["jami_savdo"] or 0

    # Барча кунлар учун умумий товар кирими (Сумма розничн бўйича)
    income_total = conn.execute(
        "SELECT SUM(summa_roznichn) AS jami_tovar_kirimi FROM product_income"
    ).fetchone()["jami_tovar_kirimi"] or 0

    # Барча кунлар учун умумий чиқимлар
    expenses_total = conn.execute(
        "SELECT SUM(miqdor) AS jami_harajatlar FROM expenses"
    ).fetchone()["jami_harajatlar"] or 0

    # Товар қолдиғи ҳисоблаш
    tovar_qoldigi_oxirida = (
        tovar_qoldigi_boshida + income_total - sales_total - expenses_total
    )


    bugun = datetime.now().strftime("%Y-%m-%d")

    # Бугунги сана учун мавжуд ҳисоботни текшириш
    existing_hisobot = conn.execute(
        "SELECT id FROM hisobot WHERE sana = ?", (bugun,)
    ).fetchone()

    if existing_hisobot:
        # Агар ҳисобот мавжуд бўлса, уни янгилаш
        conn.execute(
            """
            UPDATE hisobot SET
            jami_savdo = ?,
            jami_tovar_kirimi = ?,
            jami_harajatlar = ?,
            tovar_qoldigi_boshida = ?,
            tovar_qoldigi_oxirida = ?
            WHERE id = ?
            """,
            (
                sales_total,
                income_total,
                expenses_total,
                tovar_qoldigi_boshida,
                tovar_qoldigi_oxirida,
                existing_hisobot["id"],
            ),
        )
    else:
        # Агар ҳисобот мавжуд бўлмаса, янги ҳисоботни яратиш
        conn.execute(
            """
            INSERT INTO hisobot
            (sana, jami_savdo, jami_tovar_kirimi, jami_harajatlar, tovar_qoldigi_boshida, tovar_qoldigi_oxirida)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (
                bugun,
                sales_total,
                income_total,
                expenses_total,
                tovar_qoldigi_boshida,
                tovar_qoldigi_oxirida,
            ),
        )

    conn.commit()

    # Ҳисобот маълумотларини олиш
    hisobotlar = conn.execute(
        "SELECT * FROM hisobot ORDER BY id DESC LIMIT 1"
    ).fetchall()

    latest_balance_row = conn.execute(
        "SELECT tovar_qoldigi_boshida FROM hisobot ORDER BY id DESC LIMIT 1"
    ).fetchone()
    tovar_qoldigi_boshida = (
        latest_balance_row["tovar_qoldigi_boshida"] if latest_balance_row else 0
    )

    conn.close()

    return render_template("hisobot.html", hisobotlar=hisobotlar, tovar_qoldigi_boshida=tovar_qoldigi_boshida)

@bp.route("/update_tovar_qoldigi", methods=["POST"])
def update_tovar_qoldigi():
    ADMIN_PASSWORD = "1234"  # Админ пароли

    # Киритилган қийматларни олиш
    tovar_qoldigi_boshida = request.form.get("tovar_qoldigi_boshida", "").strip()
    entered_password = request.form.get("admin_password", "").strip()

    # Паролни текшириш
    if entered_password != ADMIN_PASSWORD:
        return "❌ Хатолик: Парол нотўғри!"

    # Киритилган қийматни float'га айлантириш
    try:
        tovar_qoldigi_boshida = float(tovar_qoldigi_boshida.replace(",", "."))
    except ValueError:
        return "❌ Хатолик: Фақат рақам киритинг!"

    conn = get_db_connection()

    # ❗ Фақат энг БИРИНЧИ ёзувни янгилаймиз
    first_hisobot = conn.execute(
        "SELECT id FROM hisobot ORDER BY id ASC LIMIT 1"
    ).fetchone()

    if first_hisobot:
        conn.execute(
            "UPDATE hisobot SET tovar_qoldigi_boshida = ? WHERE id = ?",
            (tovar_qoldigi_boshida, first_hisobot["id"])
        )
        conn.commit()

    conn.close()
    return redirect(url_for("routes.hisobot_page"))



@bp.route("/update_old_balance", methods=["POST"])
def update_old_balance():
    conn = get_db_connection()
    new_balance = request.form.get("old_balance", type=float)
    conn.execute("UPDATE hisobot SET old_balance = ? WHERE id = (SELECT MAX(id) FROM hisobot)", (new_balance,))
    conn.commit()
    conn.close()
    return redirect(url_for("routes.hisobot_page"))

# Савдони ўчириш учун
@bp.route("/delete_sales/<int:id>", methods=["POST"])
def delete_sales(id):
    conn = get_db_connection()
    conn.execute("DELETE FROM sales WHERE id = ?", (id,))
    log_action(session["user_id"], session["username"], "Ўчирилди", "sales", record_id=id, details=details)
    conn.commit()
    conn.close()
    return redirect(url_for("routes.index"))

# Чиқимни ўчириш учун
@bp.route("/delete_expenses/<int:id>", methods=["POST"])
def delete_expenses(id):
    conn = get_db_connection()
    conn.execute("DELETE FROM expenses WHERE id = ?", (id,))
    log_action(session["user_id"], session["username"], "Ўчирилди", "expenses", record_id=id, details=details)
    conn.commit()
    conn.close()
    return redirect(url_for("routes.expenses"))

# Товар киримини ўчириш учун
@bp.route("/delete_product_income/<int:id>", methods=["POST"])
def delete_product_income(id):
    conn = get_db_connection()
    conn.execute("DELETE FROM product_income WHERE id = ?", (id,))
    log_action(session["user_id"], session["username"], "Ўчирилди", "product_income", record_id=id, details=details)
    conn.commit()
    conn.close()
    return redirect(url_for("routes.product_income"))


@bp.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]

        conn = get_db_connection()
        user = conn.execute("SELECT * FROM users WHERE username = ?", (username,)).fetchone()
        if user and check_password_hash(user["password"], password):
            # ✅ Login муваффақиятли
            session["user_id"] = user["id"]
            session["username"] = user["username"]
            session["role"] = user["role"]
            flash("Хуш келибсиз!", "success")
            return redirect(url_for("routes.index"))
        else:
            flash("Логин ёки парол нотўғри!", "danger")

    return render_template("login.html")

@bp.route("/admin")
@login_required
@admin_required
def admin_panel():
    if session.get("role") != "admin":
        flash("Рухсат йўқ!", "danger")
        return redirect(url_for("routes.index"))
    
    conn = get_db_connection()
    users = conn.execute("SELECT * FROM users").fetchall()
    conn.close()
    return render_template("admin.html", users=users)


@bp.route("/admin/add", methods=["POST"])
@login_required
def add_user():
    if session.get("role") != "admin":
        flash("Рухсат йўқ!", "danger")
        return redirect(url_for("routes.index"))

    username = request.form["username"]
    password = request.form["password"]
    hashed_password = generate_password_hash(password)
    role = request.form.get("role", "user")

    conn = get_db_connection()
    try:
        hashed_password = generate_password_hash(password)
        conn.execute("INSERT INTO users (username, password, role) VALUES (?, ?, ?)",
                    (username, hashed_password, role))
        conn.commit()
        flash("Фойдаланувчи қўшилди!", "success")
    except:
        flash("Бу фойдаланувчи аллақачон мавжуд!", "danger")

    conn.close()
    return redirect(url_for("routes.admin_panel"))


@bp.route("/admin/delete/<int:id>", methods=["POST"])
@login_required
def delete_user(id):
    if session.get("role") != "admin":
        flash("Рухсат йўқ!", "danger")
        return redirect(url_for("routes.index"))

    conn = get_db_connection()
    conn.execute("DELETE FROM users WHERE id = ?", (id,))
    log_action(session["user_id"], session["username"], "Ўчирилди", "users", record_id=id, details=details)
    conn.commit()
    conn.close()
    flash("Ўчирилди!", "success")
    return redirect(url_for("routes.admin_panel"))

@bp.route("/logout")
def logout():
    session.clear()
    flash("Тизимдан чиқдингиз!", "info")
    return redirect(url_for("routes.login"))


@bp.route("/audit_log")
@login_required
@admin_required
def audit_log_page():
    conn = get_db_connection()
    logs = conn.execute("SELECT * FROM audit_log ORDER BY timestamp DESC LIMIT 100").fetchall()
    conn.close()
    return render_template("audit_log.html", logs=logs)

@bp.route("/users_online")
@login_required
@admin_required
def users_online_view():
    conn = get_db_connection()
    users = conn.execute("""
        SELECT * FROM users_online ORDER BY last_active DESC
    """).fetchall()
    conn.close()
    return render_template("users_online.html", users=users)








