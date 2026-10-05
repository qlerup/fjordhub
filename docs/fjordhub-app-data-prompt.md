# Prompt til din apps udvikler

Kopiér teksten nedenfor til din kodeassistent:

---

Udvid vores eksisterende FjordHub-integration, så den også læser appdata uden at
ødelægge de nuværende Docker-forbrugsmålinger. Implementér og test det i denne app.

Konfigurér `FJORDHUB_BASE_URL` (FjordHubs lokale adresse, fx
`http://192.168.1.110:8091`) og `FJORDHUB_ACCESS_TOKEN` i backendens indstillinger
eller miljø. Tokenet oprettes i FjordHub med FjordFlix valgt under ekstra appdata.
Begge apps skal være opdateret, og vores backend skal kunne nå FjordHub på LAN.
Tokenet må ikke ligge i browserkode, URL'er, screenshots eller logs.

Læs API-kontrakten og eksemplet her:
https://github.com/qlerup/fjordhub/blob/main/docs/app-data-integration.md

1. Kald `GET {FJORDHUB_BASE_URL}/api/integrations/v1/resources` med header
   `Authorization: Bearer {FJORDHUB_ACCESS_TOKEN}`. Bevar de eksisterende målinger
   og læs ekstra data fra `app_data.fjordflix`. Feltet kan være helt fraværende,
   når tokenet ikke har appvalg. Man kan også hente FjordFlix alene fra
   `GET /api/integrations/v1/app-data/fjordflix` med samme header.
2. Kontrollér appobjektets eget `ok`, uafhængigt af det øverste `ok` for målingerne.
   Vis `items` som et galleri med op til 10 tilfældige posters, titel, beskrivelse,
   udgivelsesdato, genrer og rating. Metadata kan mangle; brug fornuftige fallbacks.
   Bevar UTF-8. Udvalget kan ændre sig ved hver forespørgsel. Hold eventuelt et
   galleri i 60 sekunder, mens streamstatus opdateres oftere.
3. Vis `streams` som aktuelle afspilninger med `title`, `user`, `client`, `state`,
   `mode`, `position` og `duration` (sekunder), `height` (pixels), `mbps` (Mbit/s)
   samt valgfri `video`, `audio`, `subtitle` og `encoder`. Brug `id` som nøgle og
   `movie_id` til tilknytning af titel/poster. Tom liste betyder ingen aktuelle
   streams. Afspilningsstatus udløber efter 120 sekunder uden heartbeat.
4. Posters ligger i `poster_url` på titler og streams. Hent JPEG i backend med
   samme Authorization-header og servér den til vores frontend via vores egen
   beskyttede billedrute. Almindelig `<img src=poster_url>` sender ikke tokenet.
   Tillad kun det konfigurerede FjordHub-origin og posterstier under
   `/api/integrations/v1/app-data/fjordflix/posters/`. Følg ikke redirects med
   tokenet. Cache med en rimelig størrelsesgrænse, fjern cache når token/base-URL
   ændres, og vis placeholder ved manglende poster.
5. Brug netværkstimeout, størrelsesgrænser og sekventiel polling (fx hvert 10.
   sekund uden overlap). Vis seneste gode data som forældede ved midlertidige
   fejl. Vis tydelige statusser for 401 (token ugyldigt), 403 (LAN/appadgang
   mangler), 404 (app/poster mangler eller FjordFlix skal opdateres), og 503
   (appdata utilgængelige). En fejl i FjordFlix må ikke skjule Docker-målingerne.
6. Test: gammelt svar uden `app_data`, korrekt galleri og streams, tomme lister,
   manglende metadata, dansk tekst, separat appfejl, forkert/tilbagekaldt token,
   manglende apprettighed, poster med Authorization og forsøg på et fremmed
   poster-origin. Tilpas UI'et til vores eksisterende design og mobilvisning.

---
