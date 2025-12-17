# ----------------------------
# Imports
# ----------------------------
# sqlite3: inbyggd modul för enkel filbaserad databas 
# os: för att läsa miljövariabler och filvägar
# Faker: genererar realistiska testvärden 
# Fernet: säker kryptering (externt bibliotek, del av cryptography)
import sqlite3
import os
from faker import Faker
from cryptography.fernet import Fernet
import time

# Instans av Faker — används för att skapa realistiska men påhittade namn och e-post
# Att använda en instans istället för att anropa Faker() överallt gör koden renare.
fake = Faker()

# ----------------------------
# Konfigurationshjälpare
# ----------------------------
# Funktionen get_db_path() gör att databasens plats enkelt kan konfigureras via
# miljövariabeln DATABASE_PATH. Om variabeln inte finns används en default.
# Detta underlättar när man kör i Docker eller CI: man pekar bara om DATABASE_PATH.
def get_db_path():
    return os.getenv("DATABASE_PATH", "/data/test_users.db")


# ----------------------------
# Nyckelhantering för kryptering
# ----------------------------
# load_or_create_key() läser Fernet-nyckeln från en fil (FERNET_KEY_PATH). Om filen
# inte finns skapas en ny nyckel och skrivs till filen.
#
# Viktigt:
# - Fernet-nyckeln måste förvaras säkert i en riktig miljö (t.ex. hemligt i ett
#   secret manager eller som en skyddad volym). Att spara nyckel i plain text på
#   disk är bara acceptabelt i lokala testmiljöer.
# - Om nyckeln förloras kan krypterade mejl inte dekrypteras. Om nyckeln byts
#   kommer tidigare krypterad data vara oåtkomlig.
def load_or_create_key():
    # För att enkelt ändra var nyckeln står använder vi en miljövariabel
    key_path = os.getenv("FERNET_KEY_PATH", "/data/fernet.key")

    # Om filen redan finns: läs och returnera bytes
    if os.path.exists(key_path):
        with open(key_path, "rb") as f:
            return f.read()

    # Annars: skapa en ny nyckel och skriv till fil
    key = Fernet.generate_key()
    # Skapa katalogen om den inte finns – försiktighet: i vissa fall vill
    # man inte att koden skapar kataloger automatiskt i produktionsmiljö.
    parent_dir = os.path.dirname(key_path)
    if parent_dir and not os.path.exists(parent_dir):
        try:
            os.makedirs(parent_dir, exist_ok=True)
        except Exception:
            # Om vi inte kan skapa katalog: fortsätt ändå (skrivfel kommer att bubbla upp)
            pass

    with open(key_path, "wb") as f:
        f.write(key)

    # Returnerar nyckeln som bytes
    return key

# Globalt Fernet-objekt som används för att kryptera / dekryptera e-post.
# Att skapa detta en gång är enkelt och effektivt.
FERNET = Fernet(load_or_create_key())

# ----------------------------
# Databasinitiering
# ----------------------------
# init_database() skapar tabellen users om den inte finns, och lägger in
# två testanvändare om tabellen är tom. Funktionen använder SQLite vilket
# innebär att databasen är en fil på disken.
#
# Säkerhets-/driftsnotiser:
# - I produktionssätt bör man använda migrationsverktyg (t.ex. Alembic för SQLAlchemy)
#   för att ändra scheman säkert.
# - Kontrollera filrättigheter för databasen så att inte obehöriga processer kan läsa den.
def init_database():
    """
    Skapar databasen och återställer ALLTID samma testdata.
    Detta säkerställer reproducerbar testmiljö.
    """
    db_path = os.getenv("DATABASE_PATH", "/data/test_users.db")
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # Skapa tabell
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            email TEXT NOT NULL
        )
    """)

    # Rensa tabellen varje gång (testmiljö!)
    cursor.execute("DELETE FROM users")

    # Lägg in fasta testanvändare
    users = [
        ("Anna Andersson", "anna@test.se"),
        ("Bo Bengtsson", "bo@test.se")
    ]

    cursor.executemany(
        "INSERT INTO users (name, email) VALUES (?, ?)",
        users
    )

    conn.commit()
    conn.close()


# ----------------------------
# Visa användare (enkelt)
# ----------------------------
# display_users() skriver ut alla rader i users-tabellen till stdout. Denna funktion
# är praktisk för lokala tester och demonstration.
def display_users():
    """
    Skriver ut alla användare i databasen.
    Används för att verifiera att GDPR-åtgärder fått effekt.
    """
    db_path = os.getenv("DATABASE_PATH", "/data/test_users.db")
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    cursor.execute("SELECT id, name, email FROM users")
    users = cursor.fetchall()

    print("\n--- Current users in DB ---")
    for user in users:
        print(f"ID: {user[0]}, Name: {user[1]}, Email: {user[2]}")
    print("--- End of list ---\n")

    conn.close()


# ----------------------------
# GDPR-Åtgärd 1: Anonymisering med Faker
# ----------------------------
# anonymize_users() ersätter varje användares namn och e-post med
# realistiskt utseende fake-data. Detta används ofta för att skapa
# icke-personliga test-dataset från verkliga dataset.
#
# Varför använda Faker?
# - Ger realistiska men icke-identifierande värden.
# - Enkelt att återanvända i tester utan att exponera riktiga uppgifter.
#
# Notera:
# - Anonymisering är endast korrekt om den bryter länkar till originalpersonen.
#   I detta enkla exempel ersätter vi fälten direkt i DB. I vissa scenarier vill
#   man istället skapa kopior för test och bevara originalen på säkert vis.
def anonymize_users():
    """
    GDPR-åtgärd: Anonymiserar alla användare
    genom att ersätta namn och e-post med Faker-data.
    """
    fake = Faker()
    db_path = os.getenv("DATABASE_PATH", "/data/test_users.db")
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    cursor.execute("SELECT id FROM users")
    user_ids = cursor.fetchall()

    for (user_id,) in user_ids:
        fake_name = fake.name()
        fake_email = fake.email()
        cursor.execute(
            "UPDATE users SET name = ?, email = ? WHERE id = ?",
            (fake_name, fake_email, user_id)
        )

    conn.commit()
    conn.close()

    print("✔ Users anonymized successfully.")
    display_users()
    


# ----------------------------
# GDPR-Åtgärd 2: Kryptera alla mejladresser med Fernet
# ----------------------------
# encrypt_emails() krypterar innehållet i email-fältet för varje användare
# med en symmetrisk nyckel. Detta skyddar e-postadresser vid vila (at rest).
#
# Viktigt att tänka på:
# - Fernet använder en hemlig nyckel. Om nyckeln läcker förloras konfidentialiteten.
# - Om nyckeln försvinner kan man inte återställa data (decryption misslyckas).
# - I riktiga system bör åtkomst till nycklar begränsas (t.ex. secret manager).
# - Krypterade värden i detta exempel lagras som strängar i samma kolumn.
#   Det är ofta bättre att lägga krypterade fält i separata kolumner med metadata
#   (t.ex. algoritm-version, initialization vector osv.). Fernet hanterar det mesta inbyggt.
def encrypt_emails():
    """
    GDPR-åtgärd: Krypterar alla e-postadresser i databasen.
    """
    db_path = get_db_path()
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    cursor.execute("SELECT id, email FROM users")
    users = cursor.fetchall()

    for user_id, email in users:
        encrypted_email = FERNET.encrypt(email.encode()).decode()
        cursor.execute(
            "UPDATE users SET email = ? WHERE id = ?",
            (encrypted_email, user_id)
        )

    conn.commit()
    conn.close()

    print("✔ Emails encrypted successfully.")
    display_users()

def test_email_encryption():
    """
    Enkel testfunktion som kontrollerar att
    e-postadresser SER krypterade ut.

    Regler:
    - Får INTE innehålla '@'
    - Ska innehålla '=' (typiskt för Fernet/Base64)
    """

    db_path = os.getenv("DATABASE_PATH", "/data/test_users.db")
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    cursor.execute("SELECT id, email FROM users")
    users = cursor.fetchall()

    print("\n--- Encryption test ---")

    all_ok = True

    for user_id, email in users:
        if "@" in email:
            print(f"❌ User {user_id}: FAIL (contains @)")
            all_ok = False
        elif "=" not in email:
            print(f"❌ User {user_id}: FAIL (missing '=')")
            all_ok = False
        else:
            print(f"✔ User {user_id}: OK (looks encrypted)")

    if all_ok:
        print("\n✅ Encryption test PASSED.")
    else:
        print("\n❌ Encryption test FAILED.")

    print("--- End of test ---\n")

    conn.close()


# ----------------------------
# Hjälp: Dekrypteringsfunktion (endast för test)
# ----------------------------
# decrypt_and_print_emails() visar hur man dekrypterar e-post för verifiering.
# Denna funktion bör **endast** användas i säkra testmiljöer — exponera aldrig
# dekrypterade personuppgifter i loggar i produktion.
def decrypt_and_print_emails():
    """
    Dekrypterar och skriver ut e-postadresser
    utan att ändra databasen.
    """
    db_path = get_db_path()
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    cursor.execute("SELECT id, email FROM users")
    users = cursor.fetchall()

    print("\n--- Decrypted emails ---")
    for user_id, encrypted_email in users:
        decrypted_email = FERNET.decrypt(encrypted_email.encode()).decode()
        print(f"User ID {user_id}: {decrypted_email}")

    print("--- End of list ---\n")
    conn.close()



# ----------------------------
# Huvudlöpare (körs när filen startas direkt)
# ----------------------------
# I detta exempel körs init_database(), vi skriver ut initialt innehåll
if __name__ == "__main__":
    # Initiera databasen med fasta testanvändare
    init_database()

    print("GDPR testmiljö startad.")
    print("Använd docker exec för att köra kommandon.")
    print("")
    print("Exempel:")
    print("docker exec gdpr_app python -c \"import app; app.display_users()\"")
    print("docker exec gdpr_app python -c \"import app; app.anonymize_users()\"")
    print("docker exec gdpr_app python -c \"import app; app.encrypt_emails()\"")
    print("docker exec gdpr_app python -c \"import app; app.decrypt_and_print_emails()\"")
    print("")
    print("Container is running. Press Ctrl+C to exit.")

    # Håll containern igång
    while True:
        time.sleep(1)







