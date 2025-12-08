# Personregister i testmiljön

Ett enkelt system för att hantera testdata på ett GDPR-kompatibelt sätt.

## Funktioner

- Skapa och initiera databas med testanvändare
- Visa alla användare
- Rensa all testdata (GDPR åtgärd 1)
- Anonymisera användardata (GDPR åtgärd 2)

## Installation och körning

### Förutsättningar
- Docker och Docker Compose
- Python 3.9+

### Kör med Docker

1. Klona repot:
```bash
git clone <your-repo-url>
cd personregister-testmiljo
Bygg och kör containern:
bash
docker-compose up --build
