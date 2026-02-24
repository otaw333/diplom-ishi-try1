from fastapi import FastAPI, Body, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional
import psycopg2
import os
from fastapi import WebSocket
from typing import Dict, List

app = FastAPI()
# ====== CORS ======
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "https://xorazm-job-frontend.onrender.com"
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ====== MODELS ======
class UserLogin(BaseModel):
    email: str
    password: str        


# ====== DB CONNECT ======
def get_db():
    conn = psycopg2.connect(
        os.environ.get("postgresql://diplom_db_fi53_user:jiRbphWmN9IDd6997fIVmTBF01KI8ROL@dpg-d6eq51f5r7bs73chkmrg-a/diplom_db_fi53"),
    sslmode="require")
    return conn


# ==========================
# 🔹 HAMMA VAKANSIYALAR
# ==========================
@app.get("/jobs")
def get_jobs(
    search: Optional[str] = None,
    location: Optional[str] = None
):
    conn = get_db()
    cur = conn.cursor()

    try:
        query = """
            SELECT 
                id,
                title,
                company,
                salary,
                location,
                description,
                user_id,
                vacancies_count,
                experience_required,
                payment_type,
                employment_type,
                work_mode,
                work_time,
                education_level,
                university,
                faculty,
                edu_from,
                edu_to,
                gender
            FROM jobs
            WHERE 1=1
        """

        params = []

        # 🔎 SEARCH FILTER
        if search:
            query += " AND (LOWER(title) LIKE %s OR LOWER(company) LIKE %s)"
            params.extend([
                f"%{search.lower()}%",
                f"%{search.lower()}%"
            ])

        # 📍 LOCATION FILTER
        if location:
            query += " AND LOWER(location) LIKE %s"
            params.append(f"%{location.lower()}%")

        # 🆕 Eng yangi joblar tepada
        query += " ORDER BY id DESC"

        cur.execute(query, tuple(params))
        rows = cur.fetchall()

        result = []

        for r in rows:
            result.append({
                "id": r[0],
                "title": r[1],
                "company": r[2],
                "salary": r[3],
                "location": r[4],
                "desc": r[5],
                "user_id": r[6],
                "vacancies_count": r[7],
                "experience_required": r[8],
                "payment_type": r[9],
                "employment_type": r[10],
                "work_mode": r[11],
                "work_time": r[12],
                "education_level": r[13],
                "university": r[14],
                "faculty": r[15],
                "edu_from": r[16],
                "edu_to": r[17],
                "gender": r[18],
            })

        return result

    finally:
        conn.close()





# ==========================
# 🔹 BITTA VAKANSIYA
# ==========================
@app.get("/jobs/{job_id}")
def get_job(job_id: int):

    conn = get_db()
    cur = conn.cursor()

    cur.execute("""
        SELECT id, title, company, salary, location, description, user_id
        FROM jobs WHERE id=%s
    """, (job_id,))

    r = cur.fetchone()
    conn.close()

    if not r:
        raise HTTPException(404, "Vakansiya topilmadi")

    return {
        "id": r[0],
        "title": r[1],
        "company": r[2],
        "salary": r[3],
        "location": r[4],
        "desc": r[5],
        "user_id": r[6]
    }


# ==========================
# 🔹 VAKANSIYA QO‘SHISH
# ==========================
@app.post("/jobs")
def create_job(data = Body(...)):

    conn = get_db()
    cur = conn.cursor()

    cur.execute("""
        INSERT INTO jobs
        (
            title,
            company,
            salary,
            location,
            description,
            user_id,
            experience_required,
            employment_type,
            work_mode,
            work_time,
            education_level,
            gender,
            lat,
            lng
        )
        VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
    """, (
        data["title"],
        data["company"],
        data["salary"],
        data.get("location"),
        data.get("desc", ""),
        data["user_id"],
        data.get("experience_required"),
        data.get("employment_type"),
        data.get("work_mode"),
        data.get("work_time"),
        None,  # education_level array bo‘lgani uchun keyin JSON qilamiz
        data.get("gender"),
        data.get("lat"),
        data.get("lng")
    ))

    conn.commit()
    conn.close()

    return {"message": "success"}


# ==========================
# 🔹 REGISTER
# ==========================
@app.post("/register")
def register(user: dict = Body(...)):

    conn = get_db()
    cur = conn.cursor()

    cur.execute("SELECT id FROM users WHERE email=%s", (user["email"],))
    exist = cur.fetchone()

    if exist:
        raise HTTPException(400, "Bunday email avval ro‘yxatdan o‘tgan")

    cur.execute("""
    INSERT INTO users (
        name,
        surname,
        phone,
        email,
        password,
        role,
        district,
        education,
        field,
        experience,
        salary,
        negotiable,
        about,
        english,
        russian
    )
    VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
""", (
    user.get("name"),
    user.get("surname"),
    user.get("phone"),
    user.get("email"),
    user.get("password"),
    user.get("role"),
    user.get("district"),
    user.get("education"),
    user.get("field"),
    user.get("experience"),
    user.get("salary"),
    user.get("negotiable", False),
    user.get("about"),

    # 🔥 YANGI
    user.get("english", False),
    user.get("russian", False)
))


    conn.commit()
    conn.close()

    return {"message": "ok"}



# ==========================
# 🔹 LOGIN
# ==========================
@app.post("/login")
def login(data: UserLogin):

    conn = get_db()
    cur = conn.cursor()

    cur.execute("""
        SELECT id, name, email, password, role
        FROM users
        WHERE email=%s
    """, (data.email,))

    row = cur.fetchone()
    conn.close()

    if not row:
        raise HTTPException(400, "Foydalanuvchi topilmadi")

    if row[3] != data.password:
        raise HTTPException(400, "Parol noto‘g‘ri")

    return {
        "id": row[0],
        "name": row[1],
        "email": row[2],
        "role": row[4]
    }


# ==========================
# 🔹 ARIZA YUBORISH
# ==========================
@app.post("/apply")
async def apply(data = Body(...)):

    conn = get_db()
    cur = conn.cursor()

    # duplicate check
    cur.execute("""
        SELECT id
        FROM applications
        WHERE job_id=%s AND user_id=%s
    """, (data["job_id"], data["user_id"]))

    if cur.fetchone():
        conn.close()
        raise HTTPException(400, "Siz bu ishga allaqachon ariza yuborgansiz")

    cur.execute("""
        INSERT INTO applications (job_id, user_id, message, status)
        VALUES (%s, %s, %s, 'waiting')
    """, (
        data["job_id"],
        data["user_id"],
        data["message"]
    ))

    conn.commit()

    # 🔔 owner topamiz
    cur.execute("SELECT user_id FROM jobs WHERE id=%s", (data["job_id"],))
    owner = cur.fetchone()

    conn.close()

    if owner:
        owner_id = owner[0]

        if owner_id in active_connections:
            for connection in active_connections[owner_id]:
                await connection.send_json({
                    "type": "new_application"
                })

    return {"message": "ok"}



# ==========================
# 🔹 WORKER O‘Z ARIZALARI
# ==========================
@app.get("/myapplications/{user_id}")
def get_my_applications(user_id: int):

    conn = get_db()
    cur = conn.cursor()

    cur.execute("""
        SELECT 
            a.id,
            a.job_id,
            j.title,
            j.company,
            a.status,
            a.message
        FROM applications a
        JOIN jobs j ON a.job_id = j.id
        WHERE a.user_id = %s
        ORDER BY a.id DESC
    """, (user_id,))

    rows = cur.fetchall()

    result = []
    for r in rows:
        result.append({
            "id": r[0],
            "job_id": r[1],
            "title": r[2],
            "company": r[3],
            "status": r[4],
            "message": r[5]
        })

    conn.close()
    return result


# ==========================
# 🔹 EMPLOYER — KELGAN ARIZALAR
# ==========================
@app.get("/applications/{job_id}/{owner_id}")
def get_applications(job_id: int, owner_id: int):

    conn = get_db()
    cur = conn.cursor()

    cur.execute("SELECT user_id FROM jobs WHERE id=%s", (job_id,))
    job = cur.fetchone()

    if not job or job[0] != owner_id:
        raise HTTPException(403, "Siz bu vakansiya arizalarini ko‘ra olmaysiz")

    cur.execute("""
        SELECT a.id, u.name, u.email, a.message, a.status
        FROM applications a
        JOIN users u ON u.id = a.user_id
        WHERE a.job_id = %s
    """, (job_id,))

    rows = cur.fetchall()
    conn.close()

    result = []
    for r in rows:
        result.append({
            "id": r[0],
            "name": r[1],
            "email": r[2],
            "message": r[3],
            "status": r[4]
        })

    return result


# ==========================
# 🔹 ACCEPT
# ==========================
@app.put("/applications/{app_id}/accept/{user_id}")
def accept_app(app_id: int, user_id: int):

    conn = get_db()
    cur = conn.cursor()

    cur.execute("""
        SELECT j.user_id
        FROM applications a
        JOIN jobs j ON j.id = a.job_id
        WHERE a.id=%s
    """, (app_id,))

    row = cur.fetchone()

    if not row:
        conn.close()
        raise HTTPException(404, "Ariza topilmadi")

    if row[0] != user_id:
        conn.close()
        raise HTTPException(403, "Bu ariza sizning vakansiyangizga tegishli emas!")

    cur.execute("""
        UPDATE applications
        SET status='accepted'
        WHERE id=%s
    """, (app_id,))

    conn.commit()
    conn.close()

    return {"message": "accepted"}



# ==========================
# 🔹 REJECT
# ==========================
@app.put("/applications/{app_id}/reject/{user_id}")
def reject_app(app_id: int, user_id: int):

    conn = get_db()
    cur = conn.cursor()

    cur.execute("""
        SELECT j.user_id
        FROM applications a
        JOIN jobs j ON j.id = a.job_id
        WHERE a.id=%s
    """, (app_id,))

    row = cur.fetchone()

    if not row:
        conn.close()
        raise HTTPException(404, "Ariza topilmadi")

    if row[0] != user_id:
        conn.close()
        raise HTTPException(403, "Bu ariza sizning vakansiyangizga tegishli emas!")

    cur.execute("""
        UPDATE applications
        SET status='rejected'
        WHERE id=%s
    """, (app_id,))

    conn.commit()
    conn.close()

    return {"message": "rejected"}

# ==========================
# 🔹 FAQAT O‘Z VAKANSIYALARI
# ==========================
@app.get("/myjobs/{user_id}")
def my_jobs(user_id: int):

    conn = get_db()
    cur = conn.cursor()

    cur.execute("""
        SELECT id, title, company, salary, location, description
        FROM jobs
        WHERE user_id=%s
    """, (user_id,))

    rows = cur.fetchall()
    conn.close()

    result = []

    for r in rows:
        result.append({
            "id": r[0],
            "title": r[1],
            "company": r[2],
            "salary": r[3],
            "location": r[4],
            "desc": r[5]
        })

    return result

# ==========================
# 🔹 delete
# ==========================
@app.delete("/jobs/{job_id}/{user_id}")
def delete_job(job_id: int, user_id: int):

    conn = get_db()
    cur = conn.cursor()

    cur.execute("SELECT user_id FROM jobs WHERE id=%s", (job_id,))
    row = cur.fetchone()

    if not row:
        raise HTTPException(404, "Vakansiya topilmadi")

    if row[0] != user_id:
        raise HTTPException(403, "Bu vakansiya sizga tegishli emas!")

    cur.execute("DELETE FROM jobs WHERE id=%s", (job_id,))
    conn.commit()
    conn.close()

    return {"message": "deleted"}

# ================================
# EMPLOYER UCHUN YANGI ARIZALAR SONI
# ================================

@app.get("/notifications/{user_id}")
def notifications(user_id: int):

    conn = get_db()
    cur = conn.cursor()

    cur.execute("""
        SELECT j.id, j.title, COUNT(a.id)
        FROM applications a
        JOIN jobs j ON j.id = a.job_id
        WHERE j.user_id=%s AND a.status='waiting'
        GROUP BY j.id, j.title
    """, (user_id,))

    rows = cur.fetchall()

    result = {
        "total": sum(r[2] for r in rows),
        "by_jobs": [
            {
                "job_id": r[0],
                "title": r[1],
                "count": r[2]
            } for r in rows
        ]
    }

    conn.close()
    return result

@app.get("/debug/apps")
def debug():
    conn = get_db()
    cur = conn.cursor()

    cur.execute("SELECT id, job_id, status, user_id FROM applications")
    apps = cur.fetchall()

    cur.execute("SELECT id, title, user_id FROM jobs")
    jobs = cur.fetchall()

    conn.close()

    return {
        "applications": apps,
        "jobs": jobs
    }

# ================================
# APPLICATIONLARNI KO‘RILGAN DEB BELGILASH
# ================================
@app.put("/applications/seen/{job_id}/{user_id}")
def applications_seen(job_id: int, user_id: int):

    conn = get_db()
    cur = conn.cursor()

    # faqat shu employer jobi bo‘lsa
    cur.execute("""
        UPDATE applications a
        SET status='seen'
        FROM jobs j
        WHERE a.job_id=j.id
          AND a.job_id=%s
          AND j.user_id=%s
          AND a.status='waiting'
    """, (job_id, user_id))

    conn.commit()
    conn.close()

    return {"message": "seen updated"}


# ===============================
# WEBSOCKET MANAGER
# ===============================

active_connections: Dict[int, List[WebSocket]] = {}

@app.websocket("/ws/notifications/{user_id}")
async def websocket_notifications(websocket: WebSocket, user_id: int):

    await websocket.accept()

    if user_id not in active_connections:
        active_connections[user_id] = []

    active_connections[user_id].append(websocket)

    try:
        while True:
            await websocket.receive_text()
    except Exception:
        pass
    finally:
        if user_id in active_connections:
            if websocket in active_connections[user_id]:
                active_connections[user_id].remove(websocket)


