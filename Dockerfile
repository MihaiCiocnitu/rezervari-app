# Pornim de la o imagine Python oficială, versiunea slim (mai mica ca dimensiune)
FROM python:3.9-slim

# Setam directorul de lucru in interiorul containerului
WORKDIR /app

# Copiem mai intai requirements.txt si instalam dependintele
# (facem asta separat de cod ca Docker sa poata face cache la acest layer)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copiem codul aplicatiei in container
COPY main.py .

# Expunem portul 8080 (Cloud Run foloseste 8080, nu 8000)
EXPOSE 8080

# Comanda de pornire a aplicatiei cand containerul ruleaza
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8080"]