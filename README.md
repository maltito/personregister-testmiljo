GDPR Testdata System

Ett enkelt Python/Docker-baserat system som hanterar testdata i enlighet med GDPR-krav.
Projektet innehåller anonymisering, kryptering, återställning av data, databas­initiering samt CI/CD via GitHub Actions.

📌 Syfte

Syftet med projektet är att skapa en isolerad testmiljö där testdata kan hanteras på ett GDPR-säkert sätt.
Systemet gör det möjligt att:

anonymisera användardata

kryptera e-postadresser

dekryptera krypterad data

återställa testdata

köra allt i en Docker-container

automatiskt testa kod via GitHub Actions

📁 Projektstruktur
personregister-testmiljo/
│
├── app.py                    # Huvudapplikation med GDPR-funktioner
├── requirements.txt          # Python-beroenden
├── Dockerfile                # Bygger appens container
├── docker-compose.yml        # Startar miljön och data-volym
│
├── data/                     # Persistens för DB + krypteringsnyckel (volym)
│    ├── test_users.db
│    └── fernet.key
│
└── .github/
     └── workflows/
           └── build-test.yml # CI workflow för import- och syntaxtest

⚙️ Funktioner
🔹 1. init_database()

Skapar SQLite-databas + testanvändare om de saknas.

🔹 2. anonymize_users()

Ersätter namn och e-mail med Faker-genererad testdata.

🔹 3. encrypt_emails()

Krypterar alla e-postadresser med Fernet (AES-128).

🔹 4. decrypt_and_print_emails()

Dekrypterar och visar e-postadresser (endast för test).

🔹 5. display_users()

Visar nuvarande data i databasen.

🐳 Köra projektet med Docker
1. Gå till projektmappen:
cd "C:\Users\malte\OneDrive\Dokument\GitHub\personregister-testmiljo"

2. Bygg och starta containern:
docker-compose up --build -d


Containern håller sig igång tack vare en "keep-alive"-loop i app.py.

3. Testa kommandon:


🧪 GDPR-kommandon (körs i container)
🔹 Visa nuvarande användare
docker exec gdpr_app python -c "import app; app.display_users()"

🔹 Anonymisera all data
docker exec gdpr_app python -c "import app; app.anonymize_users()"

🔹 Kryptera e-postadresser
docker exec gdpr_app python -c "import app; app.encrypt_emails()"

🔹 Dekryptera e-post (för testning)
docker exec gdpr_app python -c "import app; app.decrypt_and_print_emails()"

🔹 Återställ databasen till ursprungsdata
docker exec gdpr_app python -c "import app; app.init_database()"

🔐 GDPR-åtgärder som implementeras
Åtgärd	Implementering
Anonymisering	Faker ersätter namn + e-post
Kryptering	Fernet AES-baserad kryptering av e-post
Dekryptering	Endast för testning (internt)
Dataminimering	Möjlighet att rensa data via anonymisering
Återställning	Nyskapad testdata vid init
🔧 CI/CD – GitHub Actions

Filen .github/workflows/build-test.yml gör:

checkout av projektet

installerar Python

installerar dependencies

testar imports

kompilerar app.py för att verifiera syntax

Detta ger automatisk kvalitetskontroll vid varje push.

📝 Krav

Projektet använder:

Python 3.11

Docker / Docker Compose

SQLite

Python-bibliotek:

faker

cryptography

Installera paket lokalt:

pip install -r requirements.txt
