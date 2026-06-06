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
HTML_CONTENT = """<!DOCTYPE html>
<html lang="ro">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Rezervare Bilete</title>
<style>
  * { box-sizing: border-box; margin: 0; padding: 0; font-family: sans-serif; }
  body { background: #f4f6f9; min-height: 100vh; padding: 2rem 1rem; }
  .container { max-width: 700px; margin: 0 auto; }
  .header { display: flex; align-items: center; gap: 12px; margin-bottom: 2rem; }
  .header-icon { width: 44px; height: 44px; background: #1a73e8; border-radius: 10px; display: flex; align-items: center; justify-content: center; font-size: 22px; }
  .header h1 { font-size: 20px; font-weight: 600; color: #1a1a1a; }
  .header p { font-size: 13px; color: #666; }
  .section-title { font-size: 12px; font-weight: 600; color: #888; text-transform: uppercase; letter-spacing: .05em; margin-bottom: .75rem; }
  .events-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 12px; margin-bottom: 1.5rem; }
  .event-card { background: white; border: 2px solid #e8eaed; border-radius: 12px; padding: 1rem; cursor: pointer; transition: all .15s; }
  .event-card:hover { border-color: #aaa; }
  .event-card.selected { border-color: #1a73e8; background: #e8f0fe; }
  .event-card h3 { font-size: 14px; font-weight: 600; color: #1a1a1a; margin-bottom: 5px; }
  .event-meta { font-size: 12px; color: #666; margin-bottom: 8px; }
  .seats-badge { display: inline-block; background: #e6f4ea; color: #137333; font-size: 12px; font-weight: 500; padding: 3px 10px; border-radius: 20px; }
  .form-card { background: white; border-radius: 12px; padding: 1.5rem; border: 1px solid #e8eaed; margin-bottom: 1rem; }
  .form-row { display: grid; grid-template-columns: 1fr 1fr; gap: 12px; margin-bottom: 1rem; }
  .field label { display: block; font-size: 13px; font-weight: 500; color: #444; margin-bottom: 5px; }
  .field input { width: 100%; padding: 10px 12px; border: 1.5px solid #e0e0e0; border-radius: 8px; font-size: 14px; outline: none; }
  .field input:focus { border-color: #1a73e8; }
  .btn-reserve { width: 100%; padding: 12px; background: #1a73e8; color: white; border: none; border-radius: 8px; font-size: 15px; font-weight: 600; cursor: pointer; }
  .btn-reserve:hover { background: #1557b0; }
  .btn-reserve:disabled { background: #aaa; cursor: not-allowed; }
  .ticket { display: none; background: #e6f4ea; border: 1.5px solid #34a853; border-radius: 12px; padding: 1.25rem; }
  .ticket h2 { font-size: 16px; font-weight: 600; color: #137333; margin-bottom: 1rem; }
  .ticket-info { font-size: 13px; color: #444; margin-bottom: 5px; }
  .ticket-cod { font-family: monospace; font-size: 13px; background: white; border: 1px solid #ccc; border-radius: 8px; padding: 10px 14px; margin-top: 10px; word-break: break-all; }
  .error { display: none; background: #fce8e6; border: 1px solid #f28b82; border-radius: 8px; padding: 10px 14px; color: #c5221f; font-size: 13px; margin-top: 10px; }
  .loading { color: #666; font-size: 13px; text-align: center; padding: 1rem; }
</style>
</head>
<body>
<div class="container">
  <div class="header">
    <div class="header-icon">&#127915;</div>
    <div><h1>Rezervare Bilete</h1><p>Alege un eveniment si rezerva-ti locul</p></div>
  </div>
  <div class="section-title">Evenimente disponibile</div>
  <div class="events-grid" id="events-grid"><div class="loading">Se incarca...</div></div>
  <div class="section-title">Datele tale</div>
  <div class="form-card">
    <div class="form-row">
      <div class="field"><label>Nume complet</label><input type="text" id="inp-name" placeholder="ex: Ion Popescu"/></div>
      <div class="field"><label>Email</label><input type="email" id="inp-email" placeholder="ex: ion@email.com"/></div>
    </div>
    <button class="btn-reserve" id="btn-rez" onclick="doRezerva()">&#127903; Rezerva loc</button>
    <div class="error" id="err-box"></div>
  </div>
  <div class="ticket" id="ticket">
    <h2>&#9989; Rezervare confirmata!</h2>
    <div class="ticket-info">Eveniment: <strong id="t-event"></strong></div>
    <div class="ticket-info">Nume: <strong id="t-name"></strong></div>
    <div class="ticket-info">Status: <strong style="color:#137333">Activ</strong></div>
    <div style="font-size:12px;color:#666;margin-top:10px">Codul tau de validare:</div>
    <div class="ticket-cod" id="t-cod"></div>
  </div>
</div>
<script>
  let selId=null, selName='';
  async function loadEvents(){
    try{
      const r=await fetch('/events'); const evs=await r.json();
      const g=document.getElementById('events-grid'); g.innerHTML='';
      evs.forEach(ev=>{
        const c=document.createElement('div'); c.className='event-card';
        c.innerHTML='<h3>&#127925; '+ev.titlu+'</h3><div class="event-meta">&#128197; '+ev.data_ora.substring(0,16).replace('T',' ')+'</div><span class="seats-badge">&#129681; '+ev.locuri_disponibile+' locuri libere</span>';
        c.onclick=()=>{document.querySelectorAll('.event-card').forEach(x=>x.classList.remove('selected'));c.classList.add('selected');selId=ev.id;selName=ev.titlu;document.getElementById('btn-rez').textContent='&#127903; Rezerva loc la '+ev.titlu;};
        g.appendChild(c);
      });
      if(evs.length>0) g.firstChild.click();
    }catch(e){document.getElementById('events-grid').innerHTML='<div class="loading">Eroare la incarcare.</div>';}
  }
  async function doRezerva(){
    const name=document.getElementById('inp-name').value.trim();
    const email=document.getElementById('inp-email').value.trim();
    const err=document.getElementById('err-box'); err.style.display='none';
    if(!name||!email){err.textContent='Completeaza numele si emailul!';err.style.display='block';return;}
    if(!selId){err.textContent='Selecteaza un eveniment!';err.style.display='block';return;}
    const btn=document.getElementById('btn-rez'); btn.disabled=true; btn.textContent='Se proceseaza...';
    try{
      const r=await fetch('/reserve?nume='+encodeURIComponent(name)+'&email='+encodeURIComponent(email)+'&event_id='+selId,{method:'POST'});
      const d=await r.json();
      if(!r.ok){err.textContent=d.detail||'Eroare.';err.style.display='block';btn.disabled=false;btn.textContent='&#127903; Rezerva loc la '+selName;return;}
      document.getElementById('t-event').textContent=selName;
      document.getElementById('t-name').textContent=name;
      document.getElementById('t-cod').textContent=d.cod_bilet;
      document.getElementById('ticket').style.display='block';
      document.getElementById('ticket').scrollIntoView({behavior:'smooth'});
      btn.textContent='&#9989; Rezervare facuta!';
    }catch(e){err.textContent='Eroare de retea.';err.style.display='block';btn.disabled=false;btn.textContent='&#127903; Rezerva loc la '+selName;}
  }
  loadEvents();
</script>
</body>
</html>"""

@app.get("/", response_class=HTMLResponse)
def home():
    return HTMLResponse(content=HTML_CONTENT)

@app.get("/", response_class=HTMLResponse)
def home():
    # Deschiderea securizată cu encodare UTF-8 previne crash-ul aplicației în containerul Docker
    with open("index.html", "r", encoding="utf-8") as f:
        return HTMLResponse(content=f.read())

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