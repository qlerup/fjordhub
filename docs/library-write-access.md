# Valgfri skriveadgang til mediemapper

Opdatér både FjordHub og FjordFlix. I FjordFlix vælges **Indstillinger → Bibliotek → Proxmox-diske og storage → Mapper delt med FjordHubs LXC → Få fuld adgang**.

Guiden er kun synlig for appens administratorer og viser kommandoer. Den udfører dem ikke via HTTP eller lagerets begrænsede SSH-funktion. En Proxmox-administrator gennemgår og kører dem som root på værten.

Adgangen omfatter den viste, eksisterende bind-monterede mappe og alle dens undermapper. Vælg en særskilt montering, hvis kun en undermappe skal være skrivbar. Systemmapper, rå blok-enheder og Proxmox-volumener tilbydes ikke denne guide. Andre monteringer inde i mappen afvises.

Kommandoerne kontrollerer den aktuelle kilde, destination og konfigurationsversion, tager backup af LXC-konfigurationen og ændrer kun `ro` på det valgte `mpN`. En nødvendig LXC-genstart påvirker alle apps i denne LXC. Dernæst oprettes en særskilt Docker bind-montering til netop denne sti. Dockers overordnede `/library/server` forbliver skrivebeskyttet. Override-filen `docker-compose.fjordhub-library.yml` og `COMPOSE_FILE` bevares ved opdatering og geninstallation gennem FjordHub. Flere uafhængige mapper understøttes; overlappende Docker-monteringer afvises.

**Filrettigheder er et separat, fravalgt tilvalg.** Det kræver `acl` på Proxmox. Scriptet finder FjordFlix-brugerens faktiske UID via den kørende LXC's UID-mapping og giver læse/skrive/mappegennemgang på den valgte mappe. Det følger ikke symbolske links og ændrer ikke ejerskab. Rettigheder sikkerhedskopieres med `getfacl` inden `setfacl`. Docker userns/rootless kræver manuel opsætning og afvises. Nye filer oprettet senere af andre programmer er stadig underlagt disse programmers rettigheder.

Konfigurationsbackup ligger i `/root/fjordhub-library-backups` på Proxmox og i FjordHubs private datamappe under `library-permission-backups`. Konsollen viser den konkrete backupplacering. Hvis ACL-tilvalget er brugt, kan rettigheder gendannes med den viste `setfacl --restore=…`-kommando. Gendan kun den relevante `mpN` fra backup ved tilbagerulning; overskriv ikke andre efterfølgende LXC-ændringer. Fjern den tilsvarende Docker-volume i override-filen og genopret FjordFlix-containeren for at fjerne skriveadgangen dér.

Hvis Docker-genoprettelsen fejler, gendannes de tidligere Docker-konfigurationsfiler og den tidligere konfiguration forsøges startet. Proxmox- og eventuelle ACL-ændringer rulles ikke automatisk tilbage; backup og fejl bevares. En afbrudt guide må ikke antages at have ændret ingenting.

Til sidst testes faktisk oprettelse, skrivning, læsning og sletning af en ny midlertidig fil inde i FjordFlix. Guiden flytter eller sletter ikke mediefiler. Testen bekræfter adgang til mappen, ikke at alle gamle filer har identiske rettigheder.

Dette er en adgangsguide, ikke en ændring af FjordFlix' filfunktioner. Upload bruger fortsat appens uploadmappe, og sletning af originaler fra eksterne biblioteksmapper er fortsat blokeret i filmvisningen.

Afinstallation af FjordFlix i FjordHub bevarer alle filer på disse mounts, også efter skriveadgang er aktiveret. FjordHubs egen `scripts/uninstall.py` bevarer ligeledes mounts, Docker-volumes og filindhold. Ingen af disse afinstallationer sletter LXC-containeren eller lageret i Proxmox.

Grundlag: [Compose sammenfletter volumes efter destination](https://docs.docker.com/reference/compose-file/merge/), og [setfacl dokumenterer fysisk traversal og rettighedsmasken](https://man7.org/linux/man-pages/man1/setfacl.1.html).
