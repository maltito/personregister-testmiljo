# 1. Använd en officiell Python-bild
# -------------------------------
# "python:3.11-slim" är en liten och snabb image
# som ändå innehåller allt som behövs för att köra Python-appar.
FROM python:3.11-slim

# -------------------------------
# 2. Ange arbetskatalog för appen
# -------------------------------
# Alla kommandon körs inne i /app i containern.
WORKDIR /app

# -------------------------------
# 3. Installera SQLite
# -------------------------------
# SQLite behövs för att kunna:
# - skapa databasen
# - läsa/skriva testdata i app.py
RUN apt-get update && apt-get install -y sqlite3 && rm -rf /var/lib/apt/lists/*

# -------------------------------
# 4. Kopiera in applikationsfiler
# -------------------------------
# app.py = huvudprogrammet
# requirements.txt = Python-bibliotek
COPY app.py /app/app.py
COPY requirements.txt /app/requirements.txt

# -------------------------------
# 5. Installera Python-bibliotek
# -------------------------------
# --no-cache-dir gör installationen snabbare
RUN pip install --no-cache-dir -r requirements.txt

# -------------------------------
# 6. Skapa katalog för databas + krypteringsnyckel
# -------------------------------
# SQLite-databasen och Fernet-nyckeln kommer att sparas i /data.
# Katalogen mappas till en Docker-volym i docker-compose.yml.
RUN mkdir -p /data

# -------------------------------
# 7. Starta applikationen när containern körs
# -------------------------------
# Detta är huvudkommandot som kör app.py när containern startar.
CMD ["python", "app.py"]
