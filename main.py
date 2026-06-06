# main.py - Aplicatia principala FastAPI pentru rezervare bilete

from fastapi import FastAPI, HTTPException  # FastAPI = framework-ul web; HTTPException = erori HTTP
from uuid import uuid4                      # uuid4 genereaza coduri unice pentru bilete
import psycopg2                             # biblioteca pentru conectarea la PostgreSQL
import os                                   # pentru citirea variabilelor de mediu

# Initializam aplicatia FastAPI
app = FastAPI(title="Rezervare Bilete API")

# Functie care face conexiunea la baza de date Cloud SQL
# Credentialele vin din variabile de mediu (mai sigur decat hardcodat)
def get_connection():
    return psycopg2.connect(
        host=os.getenv("DB_HOST", "34.40.24.192"),       # IP-ul Cloud SQL
        database=os.getenv("DB_NAME", "rezervari_db"),   # numele bazei de date
        user=os.getenv("DB_USER", "postgres"),            # userul PostgreSQL
        password=os.getenv("DB_PASS", "Rezervari2026!"), # parola
        port=5432                                         # portul standard PostgreSQL
    )

# -----------------------------------------------------------------------
# ENDPOINT 1: GET /events
# Returneaza lista tuturor evenimentelor cu locuri disponibile
# -----------------------------------------------------------------------
@app.get("/events")
def get_events():
    conn = get_connection()           # deschidem conexiunea
    cursor = conn.cursor()            # cream un cursor pentru a executa SQL
    
    # Selectam evenimentele care mai au locuri libere
    cursor.execute("""
        SELECT id, titlu, data_ora, locuri_disponibile 
        FROM Events 
        WHERE locuri_disponibile > 0
    """)
    
    rows = cursor.fetchall()          # luam toate rezultatele
    cursor.close()
    conn.close()                      # inchidem conexiunea dupa ce am terminat
    
    # Transformam rezultatele intr-o lista de dictionare (format JSON)
    return [
        {
            "id": r[0],
            "titlu": r[1],
            "data_ora": str(r[2]),
            "locuri_disponibile": r[3]
        }
        for r in rows
    ]

# -----------------------------------------------------------------------
# ENDPOINT 2: POST /reserve
# Creeaza o rezervare noua pentru un utilizator la un eveniment
# -----------------------------------------------------------------------
@app.post("/reserve")
def rezerva(user_id: int, event_id: int):
    conn = get_connection()
    cursor = conn.cursor()
    
    # Verificam daca mai sunt locuri disponibile la eveniment
    cursor.execute(
        "SELECT locuri_disponibile FROM Events WHERE id = %s",
        (event_id,)
    )
    event = cursor.fetchone()
    
    # Daca evenimentul nu exista, returnam eroare 404
    if not event:
        raise HTTPException(status_code=404, detail="Evenimentul nu exista")
    
    # Daca nu mai sunt locuri, returnam eroare 400
    if event[0] <= 0:
        raise HTTPException(status_code=400, detail="Nu mai sunt locuri disponibile")
    
    # Generam un cod unic de validare pentru bilet (ex: 550e8400-e29b-41d4...)
    cod_unic = str(uuid4())
    
    # Scadem un loc disponibil din eveniment
    cursor.execute(
        "UPDATE Events SET locuri_disponibile = locuri_disponibile - 1 WHERE id = %s",
        (event_id,)
    )
    
    # Inseram biletul nou in tabela Tickets
    cursor.execute(
        """INSERT INTO Tickets (user_id, event_id, cod_validare, status) 
           VALUES (%s, %s, %s, 'activ')""",
        (user_id, event_id, cod_unic)
    )
    
    conn.commit()   # salvam modificarile in baza de date (ACID - atomicitate)
    cursor.close()
    conn.close()
    
    return {"mesaj": "Rezervare reusita!", "cod_bilet": cod_unic, "status": "activ"}

# -----------------------------------------------------------------------
# ENDPOINT 3: GET /validate/{cod}
# Verifica daca un bilet este valid pe baza codului sau unic
# -----------------------------------------------------------------------
@app.get("/validate/{cod}")
def valideaza_bilet(cod: str):
    conn = get_connection()
    cursor = conn.cursor()
    
    # Cautam biletul cu codul dat, impreuna cu detalii despre user si eveniment
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
    
    # Daca nu gasim biletul, returnam eroare 404
    if not bilet:
        raise HTTPException(status_code=404, detail="Bilet invalid sau inexistent")
    
    return {
        "valid": True,
        "bilet_id": bilet[0],
        "status": bilet[1],
        "utilizator": bilet[2],
        "eveniment": bilet[3]
    }