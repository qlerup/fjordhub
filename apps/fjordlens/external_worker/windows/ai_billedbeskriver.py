import base64
import json
import os
import re
import sys
from io import BytesIO
from pathlib import Path

import requests


# ============================================================
# STANDARDINDSTILLINGER
# ============================================================

DEFAULT_VISION_MODEL = "qwen2.5vl:7b"
MODEL = os.environ.get("OLLAMA_VISION_MODEL", DEFAULT_VISION_MODEL).strip() or DEFAULT_VISION_MODEL
OLLAMA_BASE_URL = os.environ.get("OLLAMA_HOST", "http://localhost:11434").strip()
REQUEST_TIMEOUT_SEC = 300

SUPPORTED_IMAGE_EXTENSIONS = {
    ".jpg", ".jpeg", ".png", ".webp", ".gif", ".bmp", ".tif", ".tiff", ".svg"
}
DIRECT_IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png"}
MAX_CONVERTED_IMAGE_SIDE = 2048

VISION_INSTALL_HINT = (
    "Installer en vision-model først, f.eks.:\n"
    "  ollama pull qwen2.5vl:7b\n"
    "eller en mindre model:\n"
    "  ollama pull qwen2.5vl:3b"
)


def normaliser_ollama_base_url(raw_url: str) -> str:
    url = (raw_url or "http://localhost:11434").strip().rstrip("/")
    if not url.startswith(("http://", "https://")):
        url = f"http://{url}"
    return url


OLLAMA_BASE_URL = normaliser_ollama_base_url(OLLAMA_BASE_URL)

PROMPT = """
Du analyserer et billede.
Svar på dansk.

Fokus:
1) Kort beskrivelse i 1-2 sætninger.
2) Hvad sker der i billedet.
3) Mennesker skal være hovedfokus: hvor mange, hvad laver de, og hvem er hvem.
4) Beskriv hver tydelig person separat, så billedet senere kan søges frem.
   Brug gerne visuelle søgeord som "voksen der holder barn", "barn i pool",
   "fremstår som kvinde", "fremstår som mand", "fremstår som pige" eller
   "fremstår som dreng", når billedet giver rimeligt grundlag.
   Skriv "usikkert" eller "fremstår muligvis som ..." hvis det ikke er tydeligt.
   Formuler køn som en visuel vurdering, ikke som en sikker identitet.
   Hvis du vurderer en person som kvinde/mand/pige/dreng, så brug den betegnelse
   i "kort_beskrivelse", "hvad_sker_der" og "hvad_laver_de" i stedet for kun
   at skrive "voksen" eller "barn".
   Søgeord må heller ikke ende som "voksen der holder barn", hvis du kan skrive
   mere præcist som "kvinde der holder pige".
5) Vigtige objekter og miljø.
6) Samlede søgeord: lav mange relevante søgeord og søgefraser ud fra hele billedet.
   Medtag også synonymer og nærliggende formuleringer, så billedet er let at finde,
   men kun for ting, personer, steder og handlinger der tydeligt ses i billedet.
   Gæt ikke på vand, pool, strand, sport, dyr eller objekter, hvis de ikke er synlige.
7) Usikkerheder (hvad du ikke kan se tydeligt).

Returner KUN gyldig JSON i dette format:
Ingen markdown, ingen ```json-kodeblok og ingen forklaring uden om JSON.
{
  "kort_beskrivelse": "...",
  "hvad_sker_der": "...",
  "mennesker": {
    "antal": 0,
    "hvad_laver_de": "Ingen tydelige mennesker",
    "personer": [
      {
        "label": "Person 1",
        "rolle_i_billedet": "...",
        "alderstrin": "voksen/barn/ung/ældre/usikkert",
        "visuel_koensvurdering": "fremstår som kvinde/mand/pige/dreng eller usikkert",
        "beskrivelse": "...",
        "soegeord": ["..."]
      }
    ],
    "koen_og_alder": "Ingen tydelige mennesker",
    "pige_dreng_vurdering": "Ingen tydelige børn",
    "soegeord_personer": "..."
  },
  "objekter_og_miljoe": "...",
  "samlede_soegeord": ["..."],
  "usikkerheder": "..."
}
""".strip()


# ============================================================
# INPUT OG FILHAANDTERING
# ============================================================


def vaelg_billedsti() -> Path:
    if len(sys.argv) > 1:
        raw = " ".join(sys.argv[1:]).strip().strip('"')
    else:
        print()
        print("Indtast sti til billedet, der skal analyseres:")
        raw = input("> ").strip().strip('"')

    if not raw:
        raise ValueError("Ingen sti angivet.")

    path = Path(raw).expanduser().resolve()

    if not path.exists() or not path.is_file():
        raise FileNotFoundError(f"Billedfil blev ikke fundet: {path}")

    if path.suffix.lower() not in SUPPORTED_IMAGE_EXTENSIONS:
        print(
            "Advarsel: filtypen er ikke en standard billedtype. "
            "Forsøger alligevel at sende den til modellen."
        )

    return path


def laes_billede_base64(path: Path) -> str:
    data = path.read_bytes()
    if not data:
        raise ValueError("Billedfilen er tom.")

    if path.suffix.lower() not in DIRECT_IMAGE_EXTENSIONS:
        converted = konverter_til_jpeg_hvis_muligt(path)
        if converted:
            data = converted

    return base64.b64encode(data).decode("ascii")


def konverter_til_jpeg_hvis_muligt(path: Path):
    try:
        from PIL import Image
    except ImportError:
        print(
            "Advarsel: Pillow er ikke installeret, så billedet sendes i originalformat. "
            "JPG, JPEG og PNG virker normalt direkte."
        )
        return None

    try:
        with Image.open(path) as img:
            img.seek(0)
            frame = img.copy()

        frame.thumbnail((MAX_CONVERTED_IMAGE_SIDE, MAX_CONVERTED_IMAGE_SIDE))

        if frame.mode in {"RGBA", "LA"} or (
            frame.mode == "P" and "transparency" in frame.info
        ):
            rgba = frame.convert("RGBA")
            background = Image.new("RGB", rgba.size, "white")
            background.paste(rgba, mask=rgba.getchannel("A"))
            frame = background
        else:
            frame = frame.convert("RGB")

        output = BytesIO()
        frame.save(output, format="JPEG", quality=92, optimize=True)
        print(
            "Billedet blev konverteret til JPEG, så Ollama lettere kan læse formatet."
        )
        return output.getvalue()
    except Exception as exc:
        print(f"Advarsel: kunne ikke konvertere billedet ({exc}). Sender originalfilen.")
        return None


# ============================================================
# AI-KALD
# ============================================================


def ollama_url(api_path: str) -> str:
    return f"{OLLAMA_BASE_URL}/{api_path.lstrip('/')}"


def hent_model_capabilities(model: str) -> set[str]:
    response = requests.post(
        ollama_url("/api/show"),
        json={"model": model},
        timeout=30,
    )
    response.raise_for_status()

    data = response.json()
    capabilities = data.get("capabilities") or []
    return {str(value).strip().lower() for value in capabilities if str(value).strip()}


def tjek_model_kan_laese_billeder(model: str) -> None:
    try:
        capabilities = hent_model_capabilities(model)
    except requests.HTTPError as exc:
        body = ""
        try:
            body = str(exc.response.text or "").strip()
        except Exception:
            body = ""

        status = getattr(exc.response, "status_code", None)
        body_lower = body.lower()
        if status == 404 or "not found" in body_lower or "pull" in body_lower:
            raise RuntimeError(
                f"Vision-modellen '{model}' er ikke installeret i Ollama.\n"
                f"{VISION_INSTALL_HINT}"
            ) from exc
        raise

    if capabilities and not ({"vision", "image", "images"} & capabilities):
        raise RuntimeError(
            f"Modellen '{model}' er installeret, men den understøtter ikke billeder.\n"
            "Scriptet skal bruge en vision-model, ikke en ren tekstmodel.\n"
            f"{VISION_INSTALL_HINT}"
        )


def spoerg_ollama_om_billede(image_b64: str) -> str:
    payload = {
        "model": MODEL,
        "messages": [
            {
                "role": "user",
                "content": PROMPT,
                "images": [image_b64],
            }
        ],
        "stream": False,
        "format": "json",
        "options": {
            "temperature": 0.2,
            "num_ctx": 4096,
            "num_predict": 1600,
        },
    }

    response = requests.post(
        ollama_url("/api/chat"),
        json=payload,
        timeout=REQUEST_TIMEOUT_SEC,
    )
    response.raise_for_status()

    data = response.json()
    message = data.get("message") if isinstance(data.get("message"), dict) else {}
    raw = str(message.get("content") or data.get("response") or "").strip()

    if not raw:
        raise ValueError("Modellen returnerede tomt svar.")

    return raw


def udtraek_json(raw_text: str) -> dict:
    text = str(raw_text or "").strip()
    if not text:
        raise ValueError("Modellen returnerede tomt svar.")

    try:
        parsed = json.loads(text)
        if isinstance(parsed, dict):
            return parsed
    except Exception:
        pass

    # Qwen kan finde på at pakke JSON ind i ```json ... ```.
    text = re.sub(r"^\s*```(?:json)?\s*", "", text, flags=re.IGNORECASE)
    text = re.sub(r"\s*```\s*$", "", text).strip()

    start = text.find("{")
    end = text.rfind("}") + 1

    if start == -1 or end <= start:
        raise ValueError("Kunne ikke finde JSON i modelsvaret.")

    candidate = text[start:end]
    try:
        return json.loads(candidate)
    except json.JSONDecodeError:
        repaired = re.sub(r",\s*([}\]])", r"\1", candidate)
        return json.loads(repaired)


# ============================================================
# OUTPUT
# ============================================================


def as_text(value) -> str:
    text = str(value or "").strip()
    return text if text else "-"


def as_search_words(value) -> str:
    if isinstance(value, list):
        parts = []
        seen: set[str] = set()
        for item in value:
            text = str(item).strip()
            key = fold_soegeord(text)
            if text and key and key not in seen:
                seen.add(key)
                parts.append(text)
        return ", ".join(parts) if parts else "-"
    return as_text(value)


def fold_soegeord(value) -> str:
    text = str(value or "").casefold()
    text = (
        text.replace("æ", "ae")
        .replace("ø", "oe")
        .replace("å", "aa")
        .replace("é", "e")
    )
    text = re.sub(r"[^a-z0-9]+", " ", text)
    return re.sub(r"\s+", " ", text).strip()


def soegeord_dele(value) -> list[str]:
    if isinstance(value, dict):
        parts: list[str] = []
        for item in value.values():
            parts.extend(soegeord_dele(item))
        return parts

    if isinstance(value, (list, tuple, set)):
        parts = []
        for item in value:
            parts.extend(soegeord_dele(item))
        return parts

    text = str(value or "").strip()
    if not text:
        return []

    return [
        part.strip()
        for part in re.split(r"[,;|]|\s+[–—-]\s+", text)
        if part.strip()
    ]


def tilfoej_soegeord(out: list[str], seen: set[str], value) -> None:
    for part in soegeord_dele(value):
        text = re.sub(r"\s+", " ", part.strip().lower())
        text = text.strip(" \t\r\n\"'`[]{}()")
        if not text or text == "-" or len(text) > 70:
            continue
        if re.fullmatch(r"person\s*\d+", text):
            continue
        key = fold_soegeord(text)
        if not key or key in seen:
            continue
        seen.add(key)
        out.append(text)


SOEGEORD_GRUPPER = [
    (
        ("strand", "hav", "kyst", "sand", "badeferie"),
        (
            "strand", "hav", "kyst", "sand", "badeferie", "ved vandet",
            "strandtur", "sommer", "udendørs",
        ),
    ),
    (
        ("hotel", "resort", "feriebolig", "solseng", "solstol", "parasol"),
        (
            "hotel", "resort", "ferie", "feriebillede", "feriebolig",
            "poolferie", "hotelpool", "solseng", "solstol", "parasol",
        ),
    ),
    (
        ("holder", "løfter", "bærer", "op i luften", "armene", "kaster"),
        (
            "holder", "løfter", "bærer", "holder barn", "løfter barn",
            "bærer barn", "leg med barn", "op i luften", "i armene",
        ),
    ),
    (
        ("leger", "glad", "smiler", "aktiv", "leg"),
        ("leger", "leg", "glad", "glæde", "smiler", "aktiv", "familieleg"),
    ),
    (
        ("barn", "børn"),
        ("barn", "børn", "barn i billede", "børnebillede"),
    ),
    (
        ("pige",),
        ("pige", "barn", "pige i billede", "børnebillede"),
    ),
    (
        ("dreng",),
        ("dreng", "barn", "dreng i billede", "børnebillede"),
    ),
    (
        ("kvinde",),
        ("kvinde", "dame", "voksen kvinde", "fremstår som kvinde", "person"),
    ),
    (
        ("mand",),
        ("mand", "voksen mand", "fremstår som mand", "person"),
    ),
    (
        ("voksen",),
        ("voksen", "person", "menneske"),
    ),
    (
        ("tatovering", "tatoveringer", "tattoo"),
        ("tatovering", "tatoveringer", "tattoo", "tatoveret"),
    ),
    (
        ("sol", "solskin", "udendørs", "sommer"),
        ("sol", "solskin", "udendørs", "sommer", "sommerdag", "dagslys"),
    ),
]


def tekstgrundlag_for_soegeord(parsed: dict) -> str:
    parts = [
        str(part)
        for part in soegeord_dele(parsed)
        if str(part or "").strip()
    ]
    return " ".join(parts)


def har_soegeord_trigger(folded_source: str, triggers) -> bool:
    words = set(re.findall(r"[a-z0-9]+", str(folded_source or "")))
    source = f" {folded_source} "
    for trigger in triggers:
        key = fold_soegeord(trigger)
        if not key:
            continue
        if " " in key:
            if f" {key} " in source:
                return True
            continue
        if key in words:
            return True
        if key in {"svom", "dyk"} and any(word.startswith(key) for word in words):
            return True
    return False


VAND_SOEGORD_TRIGGERS = (
    "pool",
    "bassin",
    "swimmingpool",
    "vand",
    "i vand",
    "bader",
    "bade",
    "badning",
    "svøm",
    "svømmer",
    "svømme",
    "svømning",
    "dyk",
    "dykker",
    "dykning",
    "vandleg",
    "plasker",
    "poolområde",
)


def tydelig_visuel_tekst(parsed: dict) -> str:
    if not isinstance(parsed, dict):
        return ""
    parts = [
        parsed.get("kort_beskrivelse"),
        parsed.get("hvad_sker_der"),
        parsed.get("objekter_og_miljoe"),
        parsed.get("usikkerheder"),
    ]
    mennesker = parsed.get("mennesker") if isinstance(parsed.get("mennesker"), dict) else {}
    parts.extend([
        mennesker.get("hvad_laver_de"),
        mennesker.get("koen_og_alder"),
        mennesker.get("pige_dreng_vurdering"),
    ])
    personer = mennesker.get("personer") if isinstance(mennesker.get("personer"), list) else []
    for person in personer:
        if not isinstance(person, dict):
            continue
        parts.extend([
            person.get("rolle_i_billedet"),
            person.get("beskrivelse"),
            person.get("visuel_koensvurdering"),
        ])
    return " ".join(str(part or "") for part in parts)


def fjern_ubekraeftede_vandtags(tags: list[str], parsed: dict) -> list[str]:
    visual_folded = fold_soegeord(tydelig_visuel_tekst(parsed))
    if har_soegeord_trigger(visual_folded, VAND_SOEGORD_TRIGGERS):
        return tags
    filtered: list[str] = []
    for tag in tags:
        folded = fold_soegeord(tag)
        raw = str(tag or "").casefold()
        has_water_like_text = bool(
            har_soegeord_trigger(folded, VAND_SOEGORD_TRIGGERS)
            or re.search(r"\bsv.?m", raw)
            or re.search(r"\b(pool|bassin|swimmingpool|bader|badning|dyk|plask)\b", raw)
            or re.search(r"\bi\s+vand\b|\bvand\b", raw)
        )
        if has_water_like_text:
            continue
        filtered.append(tag)
    return filtered


def label_liste(personer: list) -> list[str]:
    labels: list[str] = []
    seen: set[str] = set()
    for person in personer:
        if not isinstance(person, dict):
            continue
        label = person_visuel_label(person)
        if not label:
            continue
        key = fold_soegeord(label)
        if key and key not in seen:
            seen.add(key)
            labels.append(label)
    return labels


def opdater_samlede_soegeord(parsed: dict) -> dict:
    if not isinstance(parsed, dict):
        return parsed

    out: list[str] = []
    seen: set[str] = set()

    mennesker = parsed.get("mennesker") if isinstance(parsed.get("mennesker"), dict) else {}
    personer = mennesker.get("personer") if isinstance(mennesker.get("personer"), list) else []
    labels = label_liste(personer)
    voksen_label = next((label for label in labels if er_voksen_label(label)), "")
    barn_label = next((label for label in labels if er_barn_label(label)), "")

    def praeciser_personord(value):
        if not (voksen_label or barn_label):
            return value
        if isinstance(value, dict):
            return {key: praeciser_personord(item) for key, item in value.items()}
        if isinstance(value, (list, tuple, set)):
            return [praeciser_personord(item) for item in value]
        return erstat_generiske_personord(str(value or ""), voksen_label, barn_label)

    tilfoej_soegeord(out, seen, praeciser_personord(parsed.get("samlede_soegeord")))

    tilfoej_soegeord(out, seen, praeciser_personord(mennesker.get("soegeord_personer")))
    for key in ("pige_dreng_vurdering", "koen_og_alder", "hvad_laver_de"):
        tilfoej_soegeord(out, seen, praeciser_personord(mennesker.get(key)))

    for person in personer:
        if not isinstance(person, dict):
            continue
        for key in ("label", "rolle_i_billedet", "alderstrin", "visuel_koensvurdering", "soegeord"):
            tilfoej_soegeord(out, seen, praeciser_personord(person.get(key)))

    tilfoej_soegeord(out, seen, parsed.get("objekter_og_miljoe"))

    source = tekstgrundlag_for_soegeord(parsed)
    folded_source = f" {fold_soegeord(source)} "

    voksne = [label for label in labels if er_voksen_label(label)]
    boern = [label for label in labels if er_barn_label(label)]
    for voksen_label in voksne:
        for barn_label in boern:
            tilfoej_soegeord(out, seen, (f"{voksen_label} og {barn_label}", f"{voksen_label} med {barn_label}"))

    parsed["samlede_soegeord"] = fjern_ubekraeftede_vandtags(out, parsed)[:60]
    return parsed


def person_visuel_label(person: dict) -> str:
    koen_text = str(person.get("visuel_koensvurdering") or "").lower()
    for label in ("pige", "dreng", "kvinde", "mand"):
        if re.search(rf"\b{label}\b", koen_text):
            return label

    values = [
        person.get("alderstrin"),
        person.get("rolle_i_billedet"),
        person.get("beskrivelse"),
        as_search_words(person.get("soegeord")),
    ]
    text = " ".join(str(value or "").lower() for value in values)

    for label in ("pige", "dreng", "kvinde", "mand"):
        if re.search(rf"\b{label}\b", text):
            return label

    if re.search(r"\bbarn\b", text):
        return "barn"
    if re.search(r"\bvoksen\b", text):
        return "person"
    return ""


def ubestemt_artikel(label: str, capitalize: bool = False) -> str:
    article = "et" if label == "barn" else "en"
    text = f"{article} {label}"
    return text[:1].upper() + text[1:] if capitalize else text


def bestemt_form(label: str) -> str:
    forms = {
        "kvinde": "kvinden",
        "mand": "manden",
        "pige": "pigen",
        "dreng": "drengen",
        "barn": "barnet",
        "person": "personen",
    }
    return forms.get(label, label)


def ejefald_form(label: str) -> str:
    forms = {
        "kvinde": "kvindens",
        "mand": "mandens",
        "pige": "pigens",
        "dreng": "drengens",
        "barn": "barnets",
        "person": "personens",
    }
    return forms.get(label, f"{label}s")


def er_barn_label(label: str) -> bool:
    return label in {"pige", "dreng", "barn"}


def er_voksen_label(label: str) -> bool:
    return label in {"kvinde", "mand", "person"}


def erstat_generiske_personord(text: str, voksen_label: str, barn_label: str) -> str:
    if not isinstance(text, str) or not text.strip():
        return text

    out = text

    if voksen_label and barn_label:
        out = re.sub(
            r"\bEn voksen, der holder et barn\b",
            f"{ubestemt_artikel(voksen_label, True)}, der holder {ubestemt_artikel(barn_label)}",
            out,
        )
        out = re.sub(
            r"\ben voksen, der holder et barn\b",
            f"{ubestemt_artikel(voksen_label)}, der holder {ubestemt_artikel(barn_label)}",
            out,
        )
        out = re.sub(
            r"\bEn voksen holder et barn\b",
            f"{ubestemt_artikel(voksen_label, True)} holder {ubestemt_artikel(barn_label)}",
            out,
        )
        out = re.sub(
            r"\ben voksen holder et barn\b",
            f"{ubestemt_artikel(voksen_label)} holder {ubestemt_artikel(barn_label)}",
            out,
        )
        out = re.sub(
            r"\bvoksen der holder barn\b",
            f"{voksen_label} der holder {barn_label}",
            out,
        )

    if voksen_label:
        out = re.sub(r"\bVoksenens\b", ejefald_form(voksen_label).capitalize(), out)
        out = re.sub(r"\bvoksenens\b", ejefald_form(voksen_label), out)
        out = re.sub(r"\bVoksenen\b", bestemt_form(voksen_label).capitalize(), out)
        out = re.sub(r"\bvoksenen\b", bestemt_form(voksen_label), out)
        out = re.sub(r"\bEn voksen\b", ubestemt_artikel(voksen_label, True), out)
        out = re.sub(r"\ben voksen\b", ubestemt_artikel(voksen_label), out)
        out = re.sub(r"\bVoksen\b", voksen_label.capitalize(), out)
        out = re.sub(r"\bvoksen\b", voksen_label, out)

    if barn_label:
        out = re.sub(r"\bBarnets\b", ejefald_form(barn_label).capitalize(), out)
        out = re.sub(r"\bbarnets\b", ejefald_form(barn_label), out)
        out = re.sub(r"\bEt barn\b", ubestemt_artikel(barn_label, True), out)
        out = re.sub(r"\bet barn\b", ubestemt_artikel(barn_label), out)
        out = re.sub(r"\bBarnet\b", bestemt_form(barn_label).capitalize(), out)
        out = re.sub(r"\bbarnet\b", bestemt_form(barn_label), out)
        out = re.sub(r"\bBarn\b", barn_label.capitalize(), out)
        out = re.sub(r"\bbarn\b", barn_label, out)

    out = re.sub(r"\b(Kvinde|Mand|Pige|Dreng) person\b", r"\1", out)
    out = re.sub(r"\b(kvinde|mand|pige|dreng) person\b", r"\1", out)

    return out


def forbedr_personfokus(parsed: dict) -> dict:
    if not isinstance(parsed, dict):
        return parsed

    mennesker = parsed.get("mennesker")
    if not isinstance(mennesker, dict):
        return opdater_samlede_soegeord(parsed)

    personer = mennesker.get("personer")
    if not isinstance(personer, list):
        return opdater_samlede_soegeord(parsed)

    labels = [
        person_visuel_label(person)
        for person in personer
        if isinstance(person, dict)
    ]

    voksen_label = next((label for label in labels if er_voksen_label(label)), "")
    barn_label = next((label for label in labels if er_barn_label(label)), "")

    if not voksen_label and not barn_label:
        return opdater_samlede_soegeord(parsed)

    for key in ("kort_beskrivelse", "hvad_sker_der"):
        parsed[key] = erstat_generiske_personord(parsed.get(key, ""), voksen_label, barn_label)

    for key in ("hvad_laver_de", "koen_og_alder", "pige_dreng_vurdering"):
        mennesker[key] = erstat_generiske_personord(mennesker.get(key, ""), voksen_label, barn_label)

    soegeord_personer = mennesker.get("soegeord_personer")
    if isinstance(soegeord_personer, list):
        mennesker["soegeord_personer"] = [
            erstat_generiske_personord(str(value), voksen_label, barn_label)
            for value in soegeord_personer
        ]
    else:
        mennesker["soegeord_personer"] = erstat_generiske_personord(
            soegeord_personer or "", voksen_label, barn_label
        )

    if voksen_label and barn_label:
        mennesker["koen_og_alder"] = f"Visuel vurdering: {voksen_label} og {barn_label}."
        mennesker["pige_dreng_vurdering"] = barn_label

    for person in personer:
        if not isinstance(person, dict):
            continue

        person_label = person_visuel_label(person)
        other_label = barn_label if er_voksen_label(person_label) else voksen_label
        for key in ("label", "rolle_i_billedet", "beskrivelse"):
            person[key] = erstat_generiske_personord(person.get(key, ""), person_label if er_voksen_label(person_label) else other_label, person_label if er_barn_label(person_label) else other_label)

        soegeord = person.get("soegeord")
        if isinstance(soegeord, list):
            person["soegeord"] = [
                erstat_generiske_personord(str(value), voksen_label, barn_label)
                for value in soegeord
            ]

    return opdater_samlede_soegeord(parsed)


def person_kategori(person: dict) -> str:
    label = person_visuel_label(person)
    alderstrin = as_text(person.get("alderstrin"))

    if label and label not in {"person", "barn"}:
        if alderstrin != "-":
            return f"{label} ({alderstrin})"
        return label

    return alderstrin


def parsed_to_caption_tags(parsed: dict) -> tuple[str, list[str]]:
    if not isinstance(parsed, dict):
        return ("", [])

    parsed = opdater_samlede_soegeord(parsed)
    mennesker = parsed.get("mennesker") if isinstance(parsed.get("mennesker"), dict) else {}
    caption_parts = [
        as_text(parsed.get("caption")),
        as_text(parsed.get("kort_beskrivelse")),
        as_text(parsed.get("hvad_sker_der")),
    ]
    caption = " ".join(part for part in caption_parts if part != "-").strip()

    tags: list[str] = []

    def add_tag(value) -> None:
        text = str(value or "").strip().lower()
        if not text or text == "-":
            return
        if re.fullmatch(r"person\s*\d+", text):
            return
        if text not in tags:
            tags.append(text)

    for key in ("tags", "keywords", "soegeord", "søgeord"):
        value = parsed.get(key)
        if isinstance(value, list):
            for item in value:
                add_tag(item)
        else:
            for part in str(value or "").replace(";", ",").split(","):
                add_tag(part)

    for key in ("pige_dreng_vurdering", "koen_og_alder", "soegeord_personer"):
        value = mennesker.get(key)
        if isinstance(value, list):
            for item in value:
                add_tag(item)
        else:
            for part in str(value or "").replace(";", ",").split(","):
                add_tag(part)

    personer = mennesker.get("personer")
    if isinstance(personer, list):
        for person in personer:
            if not isinstance(person, dict):
                continue
            for key in ("label", "rolle_i_billedet", "alderstrin", "visuel_koensvurdering"):
                add_tag(person.get(key))
            soegeord = person.get("soegeord")
            if isinstance(soegeord, list):
                for item in soegeord:
                    add_tag(item)

    for key in ("objekter_og_miljoe",):
        for part in str(parsed.get(key) or "").replace(";", ",").split(","):
            add_tag(part)

    for item in parsed.get("samlede_soegeord") or []:
        add_tag(item)

    return (caption, fjern_ubekraeftede_vandtags(tags, parsed)[:80])


def print_resultat(parsed: dict) -> None:
    mennesker = parsed.get("mennesker") if isinstance(parsed, dict) else {}
    if not isinstance(mennesker, dict):
        mennesker = {}
    personer = mennesker.get("personer")
    if not isinstance(personer, list):
        personer = []

    print()
    print("=" * 70)
    print("BILLEDANALYSE")
    print("=" * 70)
    print(f"Kort: {as_text(parsed.get('kort_beskrivelse'))}")
    print()
    print(f"Hvad sker der: {as_text(parsed.get('hvad_sker_der'))}")
    print()
    print("Mennesker:")
    print(f"- Antal: {as_text(mennesker.get('antal'))}")
    print(f"- Hvad laver de: {as_text(mennesker.get('hvad_laver_de'))}")
    print(f"- Køn/alder: {as_text(mennesker.get('koen_og_alder'))}")
    print(f"- Pige/dreng: {as_text(mennesker.get('pige_dreng_vurdering'))}")
    print(f"- Søgeord: {as_search_words(mennesker.get('soegeord_personer'))}")

    for index, person in enumerate(personer, start=1):
        if not isinstance(person, dict):
            continue

        label = as_text(person.get("label"))
        if label == "-":
            label = f"Person {index}"

        print()
        print(f"{label}:")
        print(f"- Rolle: {as_text(person.get('rolle_i_billedet'))}")
        print(f"- Personkategori: {person_kategori(person)}")
        print(f"- Visuel kønsvurdering: {as_text(person.get('visuel_koensvurdering'))}")
        print(f"- Beskrivelse: {as_text(person.get('beskrivelse'))}")
        print(f"- Søgeord: {as_search_words(person.get('soegeord'))}")

    print()
    print(f"Samlede søgeord: {as_search_words(parsed.get('samlede_soegeord'))}")
    print()
    print(f"Objekter og miljø: {as_text(parsed.get('objekter_og_miljoe'))}")
    print()
    print(f"Usikkerheder: {as_text(parsed.get('usikkerheder'))}")


# ============================================================
# MAIN
# ============================================================


def main() -> None:
    print("=" * 70)
    print("AI BILLEDBESKRIVER")
    print("=" * 70)
    print(f"Model: {MODEL}")
    print(f"Ollama: {OLLAMA_BASE_URL}")

    try:
        image_path = vaelg_billedsti()
        print(f"Billede: {image_path}")

        tjek_model_kan_laese_billeder(MODEL)
        image_b64 = laes_billede_base64(image_path)
        print("Sender billede til Ollama. Første kørsel kan tage lidt tid...")
        raw = spoerg_ollama_om_billede(image_b64)

        try:
            parsed = udtraek_json(raw)
            parsed = forbedr_personfokus(parsed)
            print_resultat(parsed)
        except Exception:
            print()
            print("Modellen returnerede ikke gyldig JSON. Viser råt svar i stedet:")
            print("-" * 70)
            print(raw)

    except requests.HTTPError as exc:
        body = ""
        try:
            body = str(exc.response.text or "").strip()
        except Exception:
            body = ""

        msg_lower = body.lower()
        print()
        print("Fejl fra Ollama API.")
        if ("does not support" in msg_lower and "image" in msg_lower) or "vision" in msg_lower:
            print(
                "Den valgte model ser ud til ikke at understøtte billedinput i Ollama. "
                "Prøv en vision-model, eller skift MODEL variablen."
            )
            print(VISION_INSTALL_HINT)
        elif "not found" in msg_lower or "pull" in msg_lower:
            print(f"Modellen '{MODEL}' blev ikke fundet i Ollama.")
            print(VISION_INSTALL_HINT)
        if body:
            print(f"Detaljer: {body}")

    except requests.RequestException as exc:
        print()
        print(f"Netværks/API-fejl: {exc}")

    except Exception as exc:
        print()
        print(f"Fejl: {exc}")


if __name__ == "__main__":
    main()
