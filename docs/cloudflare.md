# Cloudflare i FjordHub

Åbn **Indstillinger → Cloudflare**, og slå administration til. Funktionen er kun tilgængelig for administratorer.

Tilføj domænet (fx `example.com`) og et Cloudflare **API-token** med:

- `Zone → Zone → Read`
- `Zone → DNS → Edit`
- Valgfrit `Account → Cloudflare Tunnel → Read` til tunneloversigten, eller `Edit` hvis tunnelregler også skal kunne ændres.

Begræns tokenet til de relevante zoner og konti. Global API Key og tunnelens forbindelsestoken understøttes ikke. Hvert domæne kan have sit eget token. Tilføj et eksisterende domæne igen for at udskifte tokenet. Adgangen kontrolleres før en tilknytning gemmes; en læseadgang kan vise DNS, men ændringer kræver DNS Edit.

Tokens gemmes krypteret i hubbens database med en nøgle afledt af FjordHubs eksisterende session secret. Tag backup af både databasen og den vedvarende secret; ved ændring af secret skal tokens indtastes igen. Tokens sendes aldrig tilbage til browseren. Deaktivering bevarer tilknytningerne, men blokerer Cloudflare-operationer. Fjern tilknytning sletter kun den lokale tilknytning, ikke eksterne DNS-poster eller tunneler.

## DNS

Oversigten indlæser eksisterende DNS-poster med paginering, uanset hvor de er oprettet. Søg, opret, rediger og slet poster. A/AAAA kontrollerer IP-format; CNAME kan pege på en tunnel. TXT, MX og øvrige understøttede typer vises også. SRV, CAA og andre strukturerede poster kan redigeres gennem datafeltet som JSON. Type kan ikke ændres på en eksisterende post; opret i stedet en ny. Proxy og TTL kan ændres, hvor posttypen understøtter det. Ukendte ekstra felter på eksisterende poster bevares gennem Cloudflares PATCH-endpoint.

## Tunneler

Oversigten viser kontoens tunneler, DNS-tilknytninger og publicerede værtsnavne på det valgte domæne. Manglende tunnelrettigheder blokerer ikke DNS-oversigten.

For en fjernstyret tunnel kan du tilføje en tunnelregel med værtsnavn og lokal serviceadresse, redigere serviceadressen og slette reglen. De øvrige værtsnavne, origin-indstillinger og afsluttende standardregel bevares. Stibaserede eller flere regler på samme værtsnavn skal redigeres hos Cloudflare. Lokalt styrede tunneler ændres i deres lokale konfigurationsfil.

**DNS og tunnelregler gemmes separat.** Efter oprettelse af en regel bruges **Opret CNAME-post** til at tilføje den proxied DNS-post, der peger på `<tunnel-id>.cfargotunnel.com`. Oversigten viser, hvis en del mangler. Sletning af DNS sletter ikke tunnelreglen og omvendt. Tunneloprettelse, tunnelsletning og overtagelse af lokale tunnelkonfigurationer er ikke en del af denne funktion.

FjordHub afviser en tunnelændring, hvis versionen er ændret siden indlæsningen. Cloudflare tilbyder ikke en atomisk transaktion mellem DNS og tunnelkonfiguration eller en version-betinget PUT; undgå samtidige ændringer af samme tunnel fra Cloudflares dashboard og FjordHub. Genindlæs før ændringer. FjordVPN ændres ikke og fortsætter med sin eksisterende opsætning.
