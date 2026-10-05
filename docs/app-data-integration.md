# Ekstra appdata via FjordHub

Administratorer vælger apps under **Indstillinger → Adgangstokens**, enten ved
oprettelse eller under **Rediger adgang til appdata** på et eksisterende token.
Docker-forbrug er altid inkluderet. Eksisterende tokens får ingen ekstra adgang,
før en administrator vælger den. Første understøttede app er FjordFlix.
Opdater både FjordHub og FjordFlix. FjordFlix skal være installeret via FjordHub.

Alle kald kræver LAN-adgang og headeren `Authorization: Bearer DIT_TOKEN`.
Tokenet giver læseadgang, inklusive seernavne i aktive streams, men ingen
afspilningskontrol, mediefiler, konti eller opsætning.

## Endpoints

- `GET /api/integrations/v1/resources`: eksisterende målinger, plus `app_data`
  for de apps, tokenet har adgang til. `app_data` udelades, når ingen apps er valgt.
- `GET /api/integrations/v1/app-data/fjordflix`: kun FjordFlix-data; uafhængig
  af Docker-målinger.
- `GET /api/integrations/v1/app-data/fjordflix/posters/{movie_id}`: JPEG via
  FjordHub. Brug den returnerede `poster_url` og samme Authorization-header.

FjordFlix returnerer højst 10 tilfældige titler med eksisterende posters fra hele
biblioteket. Er færre end 10 posters tilgængelige, returneres færre titler.
En ny forespørgsel kan give et nyt udvalg. Metadatafelter er valgfrie, da nogle
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
