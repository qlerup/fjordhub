# Ekstra appdata via FjordHub

Administratorer vælger apps under **Indstillinger → Adgangstokens**, enten ved
oprettelse eller under **Rediger appadgang** på et eksisterende token.
Docker-forbrug er altid inkluderet. Eksisterende tokens får ingen ekstra adgang,
før en administrator vælger den. Første understøttede app er FjordFlix.
Opdater både FjordHub og FjordFlix. FjordFlix skal være installeret via FjordHub.

Alle kald kræver LAN-adgang og headeren `Authorization: Bearer DIT_TOKEN`.
Appdata giver læseadgang, inklusive seernavne i aktive streams, men ingen
afspilningskontrol, mediefiler, konti eller opsætning. Opdateringsadgang er
en separat rettighed, som administratoren skal vælge pr. app.

## Opdateringsadgang

Under **Opdateringsadgang** vælges installerede apps og eventuelt **FjordHub**.
Det kan også ændres på et eksisterende token under **Rediger appadgang**.
Eksisterende tokens får ingen opdateringsrettigheder automatisk. Appdata og
opdatering vælges uafhængigt; også apps uden indholdsdeling kan opdateres.

Alle nedenstående kald bruger samme Bearer-token og kræver LAN-adgang:

- `GET /api/integrations/v1/updates`: `{ "ok": true, "updates": { "fjordflix": { ... } } }`.
  Kun de apps, tokenet har opdateringsadgang til, vises.
- `GET /api/integrations/v1/updates/{app_id}/status`: status for én app.
- `POST /api/integrations/v1/updates/{app_id}/check`: tjek seneste version.
- `POST /api/integrations/v1/updates/{app_id}/start`: giv besked om, at den valgte
  app må opdatere nu. FjordHub bruger `app_id=fjordhub` og sin updater-service.
  Der accepteres ingen kommando, sti, repo, URL eller oprydningsvalg fra klienten.

Status indeholder `app_id`, `ok`, `state`, `update_available`, `running` og
eventuelt `label`, `available`, `dirty`, `current_rev`, `remote_rev` og tidspunkter.
En accepteret start returnerer HTTP 202 og `state=updating`, `running=true`.
Poll status, eksempelvis hvert 30–60 sekund normalt og hvert 5 sekund under en
opdatering. Når `update_available=true`, kan klientappen vise en opdateringsknap;
først når brugeren vælger den, sendes POST til `start`. Ingen automatisk installation
sker ved et statuskald. Dette er polling, ikke en webhook eller push-abonnement.

`GET /api/integrations/v1/resources` indeholder også `updates`, når tokenet har
opdateringsadgang. Det separate status-endpoint virker uafhængigt af Docker-målinger.
HTTP 401 betyder ugyldigt/inaktivt/tilbagekaldt/udløbet token, 403 manglende rettighed
eller adgang uden for LAN, 404 manglende installation, 409 igangværende opdatering
eller blokerende filflytning. FjordHub kan genstarte under sin egen opdatering:
behold sidste status, håndter midlertidige forbindelsesfejl og genoptag polling.
Tokenets appvalg gemmes i databasen og bevares efter genstart.

## Endpoints

- `GET /api/integrations/v1/resources`: eksisterende målinger, plus `app_data`
  for de apps, tokenet har adgang til. `app_data` udelades, når ingen apps er valgt.
- `GET /api/integrations/v1/app-data/fjordflix`: kun FjordFlix-data; uafhængig
  af Docker-målinger.
- `GET /api/integrations/v1/app-data/fjordflix/posters/{movie_id}`: JPEG via
  FjordHub. Brug den returnerede `poster_url` og samme Authorization-header.

FjordFlix returnerer de 10 senest tilføjede film/serier fra biblioteket,
sorteret med nyeste først efter tilføjelsestidspunktet (upload eller import).
Alle afsnit og sæsoner fra samme serie tæller som én titel. Seriens placering
følger dens senest tilføjede afsnit, og `title` er seriens navn. `id` og
`poster_url` bruger det seneste afsnit, så billedadgangen er uændret. Serier
har ikke `season` eller `episode` i denne liste; aktive streams beskriver
stadig den konkrete afspilning. `library_count` tæller fortsat mediefiler.
Er biblioteket mindre end 10 titler, returneres alle. En titel med en manglende
poster er stadig med; billedkaldet kan returnere 404, så vis en placeholder.
Udvalget ændres, når titler tilføjes eller fjernes. Bevar rækkefølgen i `items`.
Metadatafelter er valgfrie, da nogle
titler ikke er identificeret i TMDB. `streams` indeholder aktuelle afspilninger
(også pause/buffering), op til 100. Afspilninger uden heartbeat udløber efter 120
sekunder; ved genstart er listen tom, indtil klienterne igen registrerer afspilning.
`position` og `duration` er sekunder, `height` er pixels, `mbps` er Mbit/s.

Eksempel på svaret fra det separate FjordFlix-endpoint; samme objekt ligger under
`app_data.fjordflix` i ressource-endpointet:

```json
{
  "ok": true,
  "generated_at": "2026-10-05T20:00:00+00:00",
  "library_count": 140,
  "items": [{
    "id": "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa",
    "title": "Eksempelfilm",
    "overview": "Beskrivelse af filmen",
    "release_date": "2025-01-01",
    "genres": ["Drama"],
    "rating": 8.1,
    "media_type": "movie",
    "poster_url": "http://192.168.1.110:8091/api/integrations/v1/app-data/fjordflix/posters/aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa"
  }],
  "streams": [{
    "id": "playback-id",
    "movie_id": "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa",
    "title": "Eksempelfilm",
    "user": "Anna",
    "client": "Browser",
    "state": "playing",
    "mode": "Direct Play",
    "position": 120,
    "duration": 7200,
    "height": 1080,
    "mbps": 8,
    "encoder": "Original",
    "poster_url": "http://192.168.1.110:8091/api/integrations/v1/app-data/fjordflix/posters/aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa"
  }]
}
```

Streams kan også indeholde `video`, `audio` og `subtitle` med codec- og
sporoplysninger. Serieindhold kan have `series_title`, `season` og `episode`.

## Fejl og opdatering

401 betyder ugyldigt/udløbet/tilbagekaldt token. 403 betyder manglende appadgang
eller en forespørgsel uden for LAN. 404 betyder manglende app/poster eller en ældre
FjordFlix-version. 503 betyder utilgængelige appdata. Svar bruger `Cache-Control:
no-store`. Tomme `items`/`streams` med `ok: true` er normale tomme resultater.

En utilgængelig app giver `app_data.fjordflix = {"ok": false, "error": "…",
"status": 503}`. Andre målinger virker fortsat; HTTP-status og det øverste `ok`
beskriver Docker-målingerne. Kontrollér derfor altid appens eget `ok`.

Hent sekventielt med fx 10 sekunders interval og undgå overlappende forespørgsler.
Behold seneste gode resultat med en markering af, at det er forældet, ved netværksfejl.
Tokenet skal opbevares i den anden apps backend. En webfrontend bør hente data og
billeder gennem sin egen backend; der gives ikke CORS-adgang til andre origins.
