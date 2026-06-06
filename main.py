MAIN_PY = '''
# main.py - Microserviciu REST API pentru rezervare bilete cu interfata web

from fastapi import FastAPI, HTTPException
from fastapi.responses import HTMLResponse
from uuid import uuid4
import psycopg2
import os

app = FastAPI(title="Rezervare Bilete API")

# Functie de conectare la Cloud SQL PostgreSQL
def get_connection():
    return psycopg2.connect(
        host=os.getenv("DB_HOST", "34.40.24.192"),
        database=os.getenv("DB_NAME", "rezervari_db"),
        user=os.getenv("DB_USER", "postgres"),
        password=os.getenv("DB_PASS", "Rezervari2026!"),
        port=5432
    )

# -----------------------------------------------------------------------
# ENDPOINT 1: GET /
# Serveste interfata web HTML pentru utilizatori
# -----------------------------------------------------------------------
@app.get("/", response_class=HTMLResponse)
def home():
    return HTMLResponse(content=open("index.html").read())

# -----------------------------------------------------------------------
# ENDPOINT 2: GET /events
# Returneaza lista evenimentelor cu locuri disponibile (folosit de UI)
# -----------------------------------------------------------------------
@app.get("/events")
def get_events():
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT id, titlu, data_ora, locuri_disponibile
        FROM Events WHERE locuri_disponibile > 0
    """)
    rows = cursor.fetchall()
    cursor.close()
    conn.close()
    return [{"id": r[0], "titlu": r[1], "data_ora": str(r[2]), "locuri_disponibile": r[3]} for r in rows]

# -----------------------------------------------------------------------
# ENDPOINT 3: POST /reserve
# Accepta nume si email (nu mai cere user_id manual)
# Creeaza userul daca nu exista, apoi emite biletul
# -----------------------------------------------------------------------
@app.post("/reserve")
def rezerva(nume: str, email: str, event_id: int):
    conn = get_connection()
    cursor = conn.cursor()

    # Cauta sau creeaza utilizatorul dupa email
    cursor.execute("SELECT id FROM Users WHERE email = %s", (email,))
    user = cursor.fetchone()
    if not user:
        # Daca emailul nu exista, cream un user nou automat
        cursor.execute(
            "INSERT INTO Users (nume, email) VALUES (%s, %s) RETURNING id",
            (nume, email)
        )
        user_id = cursor.fetchone()[0]
    else:
        user_id = user[0]

    # Verifica daca mai sunt locuri la eveniment
    cursor.execute("SELECT locuri_disponibile FROM Events WHERE id = %s", (event_id,))
    event = cursor.fetchone()
    if not event:
        raise HTTPException(status_code=404, detail="Evenimentul nu exista")
    if event[0] <= 0:
        raise HTTPException(status_code=400, detail="Nu mai sunt locuri disponibile")

    # Genereaza cod unic de validare pentru bilet
    cod_unic = str(uuid4())

    # Scade un loc si insereaza biletul - operatie atomica
    cursor.execute(
        "UPDATE Events SET locuri_disponibile = locuri_disponibile - 1 WHERE id = %s",
        (event_id,)
    )
    cursor.execute(
        "INSERT INTO Tickets (user_id, event_id, cod_validare, status) VALUES (%s, %s, %s, 'activ')",
        (user_id, event_id, cod_unic)
    )
    conn.commit()
    cursor.close()
    conn.close()

    return {"mesaj": "Rezervare reusita!", "cod_bilet": cod_unic, "status": "activ"}

# -----------------------------------------------------------------------
# ENDPOINT 4: GET /validate/{cod}
# Verifica daca un bilet este valid dupa codul UUID
# -----------------------------------------------------------------------
@app.get("/validate/{cod}")
def valideaza_bilet(cod: str):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT t.id, t.status, u.nume, e.titlu
        FROM Tickets t
        JOIN Users u ON t.user_id = u.id
        JOIN Events e ON t.event_id = e.id
        WHERE t.cod_validare = %s
    """, (cod,))
    bilet = cursor.fetchone()
    cursor.close()
    conn.close()
    if not bilet:
        raise HTTPException(status_code=404, detail="Bilet invalid sau inexistent")
    return {"valid": True, "bilet_id": bilet[0], "status": bilet[1], "utilizator": bilet[2], "eveniment": bilet[3]}

# -----------------------------------------------------------------------
# ENDPOINT 5: GET /health
# Verifica starea serviciului
# -----------------------------------------------------------------------
@app.get("/health")
def health_check():
    return {"status": "ok", "versiune": "3.0"}
'''
print(MAIN_PY)