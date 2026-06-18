# FjordParcel

Self-hosted pakke-tracker der automatisk scanner dine mails og samler tracking-information fra DAO, PostNord, GLS og Bring på ét sted.

## Funktioner

- **Automatisk mailscanning** — kobler til Hotmail/Outlook eller Gmail via OAuth og finder pakker i dine mails
- **Live tracking** — henter status direkte fra fragtfirmaernes egne API'er
- **Understøttede fragtfirmaer** — DAO, PostNord, GLS, Bring
- **Automatisk baggrundsopdatering** — valgfrit interval til scanning og tracking-refresh
- **Brugeradministration** — opret admin- og brugerkonti med hashede adgangskoder
- **Rollebaseret adgang** — admins har fuld adgang; brugere ser kun pakker
- **Kører i Docker** — enkelt setup med docker compose

## Kom i gang

### Krav

- [Docker](https://www.docker.com/products/docker-desktop/) og Docker Compose

### Installation

```bash
git clone https://github.com/<dit-brugernavn>/fjordparcel.git
cd fjordparcel
```

Opret en `.env`-fil:

```env
SECRET_KEY=skift-denne-til-noget-tilfaeldigt-og-hemmeligt
PUBLIC_BASE_URL=http://localhost:8096
```

Start appen:

```bash
docker compose up -d
```

Åbn `http://localhost:8096` og opret den første admin-bruger.

### Opdatering

```bash
docker compose up --build -d
```

## Konfiguration

| Variabel          | Beskrivelse                                                        |
|-------------------|--------------------------------------------------------------------|
| `SECRET_KEY`      | Flask session-nøgle — brug en lang, tilfældig streng i produktion |
| `PUBLIC_BASE_URL` | Valgfri fallback for appens offentlige URL. Kan ændres i databasen fra **Indstillinger → Mails**. |
| `DATA_DIR`        | Host-sti til data-mappen. Fresh setup sætter den absolut, så in-app updateren genstarter med samme database-mount. |
| `APP_ENCRYPTION_KEY` | Valgfri [Fernet](https://cryptography.io/en/latest/fernet/)-nøgle til kryptering af tokens. Genereres automatisk og gemmes lokalt hvis den ikke sættes. |

Data (database, tokens) gemmes som standard i `./data/` og bevares på tværs af genstart.

## Mailopsætning

### Microsoft (Hotmail / Outlook)

1. Opret en app-registrering i [Azure-portalen](https://portal.azure.com/#view/Microsoft_AAD_RegisteredApps)
2. Tilføj redirect-URI: `<PUBLIC_BASE_URL>/auth/microsoft/callback`
3. Giv delegeret tilladelse: `IMAP.AccessAsUser.All` (fra Office 365 Exchange Online)
4. Gem klient-ID og klienthemmelighed under **Indstillinger → Mails → Konfigurér Hotmail**

### Gmail

1. Opret et OAuth 2.0-klient-ID i [Google Cloud Console](https://console.cloud.google.com/)
2. Aktiver Gmail API og tilføj scope: `https://www.googleapis.com/auth/gmail.readonly`
3. Tilføj redirect-URI: `<PUBLIC_BASE_URL>/auth/google/callback`
4. Gem klient-ID og klienthemmelighed under **Indstillinger → Mails → Konfigurér Gmail**

> Gmail read-scopes er klassificeret som "restricted" af Google. Til privat brug: hold OAuth-appen i testtilstand og tilføj din Gmail-adresse som testbruger.

## Projektstruktur

```
fjordparcel/
├── app.py              # Flask-routes og request-logik
├── tracking.py         # Parsing og tracking-opslag pr. fragtfirma
├── storage.py          # SQLite-adgang (pakker, brugere, konfiguration)
├── mail_services.py    # Fælles mailscanning-logik
├── imap_mail.py        # Microsoft OAuth + IMAP
├── gmail_mail.py       # Google OAuth + Gmail API
├── app_config.py       # Indstillinger og kryptering
├── templates/          # Jinja2 HTML-templates
├── static/             # CSS, JS, logoer
├── tests/              # pytest-tests
├── Dockerfile
└── docker-compose.yml
```

## Tests

```bash
pytest
```

## Teknologier

[Flask](https://flask.palletsprojects.com/) · [SQLite](https://www.sqlite.org/) · [Gunicorn](https://gunicorn.org/) · [Docker](https://www.docker.com/)

## Licens

MIT
