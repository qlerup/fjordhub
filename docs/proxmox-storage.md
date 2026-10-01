# FjordHub og Proxmox-lager

Førstegangsopsætningen har tre trin: konto, valgfri email og valgfri lageradgang.
**Spring over** afslutter lagertrinnet uden at tilslutte mapper. Det kan åbnes igen
under **Indstillinger → Lageradgang**. Eksisterende brugere bliver ikke tvunget
gennem førstegangsopsætningen igen.

## Ny installation på Proxmox

Kør på Proxmox-værten som root (amd64). Scriptet opretter en ny Debian 13 LXC med
Docker og FjordHub samt automatisk, begrænset lageradgang:

```bash
setup_dir=$(mktemp -d /tmp/fjordhub-setup.XXXXXX)
git clone --depth 1 https://github.com/qlerup/fjordhub.git "$setup_dir"
bash "$setup_dir/scripts/install-proxmox.sh"
```

Standarder: ledigt CTID, `local-lvm`, templates på `local`, bro `vmbr0`, DHCP,
24 GiB disk, 2 CPU og 2 GiB RAM. Kan ændres via `CTID`, `STORAGE`,
`TEMPLATE_STORAGE`, `BRIDGE`, `DISK_GIB` og `HOST_IP`. Webadressen er LXC'ens IP,
port 8091. Scriptet ændrer ingen eksisterende VPN- eller app-containere.
Hvis installationen fejler efter oprettelse, behold det viste CTID og undersøg
fejlen; kør ikke blindt installeren igen og opret endnu en LXC.

## Eksisterende FjordHub, også installeret gennem MediaHub

En almindelig app-opdatering kan ikke give sig selv nye Proxmox-rettigheder.
Opdatér FjordHub først. Kør derefter følgende engangsopsætning på Proxmox-værten.
Erstat `1000`, IP-adressen og eventuelt `/opt/fjordhub` med din installation:

```bash
setup_dir=$(mktemp -d /tmp/fjordhub-setup.XXXXXX)
git clone --depth 1 https://github.com/qlerup/fjordhub.git "$setup_dir"
python3 "$setup_dir/scripts/configure_proxmox.py" 1000 --host 192.168.1.250 --directory /opt/fjordhub
```

Dette genopretter FjordHub-containeren med den nye forbindelse og erstatter dens
Proxmox-inventory-login med en separat read-only PVEAuditor-token. Credentials
lagres privat; de vises ikke i guiden. Scriptet kræver en eksisterende FjordHub
med persistent `/data` bind-mount. Proxmox' SSH-port skal kunne nås fra LXC'en.
MediaHubs egen installer bruger endnu ikke denne FjordHub-installer automatisk.

## Vælg medier i FjordFlix

Opdatér også FjordFlix. Åbn **Indstillinger → Bibliotek → Proxmox-diske og storage**.
Under **Tilgængelige lagre på Proxmox** vælger du **Tilslut lager**, bekræfter
genstarten og venter på status. FjordHubs LXC og dens apps kan genstarte. Vælg
derefter **Vælg mappe** og tilføj mediemappen til biblioteket. Flere lagre og
mapper kan tilføjes. Filerne indekseres og streames fra kilden uden import/kopi.

Automatisk tilslutning understøtter faktiske mounts under `/mnt`, `/media` og
`/srv`: mergerfs, ext4, XFS, Btrfs, ZFS, NFS og CIFS. FUSE/mergerfs kræver
`allow_other`, og filrettigheder skal tillade læsning fra den unprivilegerede LXC.
Andre Proxmox-storages og rå diske vises fortsat i inventory, men en virtuel
disk/pool uden et monteret filsystem kan ikke tilsluttes som mediemappe.

Nye mounts oprettes med `ro=1,backup=0` under `/mnt/fjordflix/pool-…`.
Eksisterende mount-numre overskrives ikke. Jobstatus og konfigurationsbackup
bevares på værten under `/var/lib/fjordhub-storage/CTID`. Ved fejl kontrolleres
status og backup før nyt forsøg; en afbrudt operation kan have ændret konfigurationen.
En systemd-startkontrol og mount-afhængigheder sikrer, at LXC'en ikke starter med
en tom underliggende mappe, hvis et tilsluttet lager mangler. Sørg for, at
værtslageret er konfigureret til at blive monteret ved boot.

Forbindelsen bruger en SSH-nøgle med `restrict` og en fast forced command for ét
CTID samt pinned host key. Appen kan kun liste lagre og anmode om tilslutning af
et identificeret lager. Den kan ikke sende vilkårlige kommandoer, stier eller
CTID'er, og kan ikke aktivere skriveadgang. Skriveadgang kræver fortsat den
separate **Få fuld adgang**-guide, som administratoren selv kører på værten.
Afinstallation bevarer mountenes filer.
