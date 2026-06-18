import html
import re
import unicodedata
from urllib.parse import quote_plus, unquote_plus


CONTEXT_KEYWORDS = {
    "tracking",
    "track",
    "trackid",
    "track-id",
    "shipment",
    "parcel",
    "package",
    "delivery",
    "courier",
    "consignment",
    "pakke",
    "pakkenr",
    "pakkenummer",
    "pakkesporing",
    "sporing",
    "forsendelse",
    "forsendelses-id",
    "forsendelsesid",
    "levering",
    "kolli",
    "kollinummer",
    "stregkode",
    "e-label",
    "dhl",
    "ups",
    "fedex",
    "gls",
    "postnord",
    "post nord",
    "bring",
    "dao",
    "dao.as",
    "daohome",
    "daoshop",
    "instabox",
    "budbee",
}

SUPPORTED_SCAN_CARRIERS = ("DAO", "PostNord", "Bring", "GLS", "FedEx")

UPS_RE = re.compile(r"\b1Z[0-9A-Z][0-9A-Z\s-]{15,24}\b", re.IGNORECASE)
S10_RE = re.compile(r"\b[A-Z]{2}\s?\d(?:[\s-]?\d){8}\s?[A-Z]{2}\b", re.IGNORECASE)
NUMERIC_RE = re.compile(r"\b(?:\d[\s-]?){8,24}\b")
ALNUM_TOKEN_RE = re.compile(r"\b(?=[A-Z0-9]{8,24}\b)(?=[A-Z0-9]*\d)[A-Z0-9]+\b", re.IGNORECASE)
URL_VALUE_RE = re.compile(
    r"(?:stregkode|shipmentid|shipment-id|match|parcelnumber|parcel-number|trackingnumber|tracking-number|q)="
    r"([A-Z0-9][A-Z0-9-]{7,30})",
    re.IGNORECASE,
)
LABEL_VALUE_RE = re.compile(
    r"(?:tracking(?:\s*number)?|track\s*id|trackid|pakkenr\.?|pakkenummer|pakkekode|stregkode|"
    r"e-label|forsendelses[-\s]?id|forsendelsesnummer|kollinummer|shipment(?:\s*(?:number|id))?|"
    r"parcel(?:\s*number)?)"
    r"(?:[\s:#-]|er|is){0,16}"
    r"("
    r"1Z[0-9A-Z][0-9A-Z\s-]{15,24}"
    r"|[A-Z]{2}\s?\d(?:[\s-]?\d){8}\s?[A-Z]{2}"
    r"|(?:\d[\s-]?){8,24}"
    r")",
    re.IGNORECASE,
)
PICKUP_CODE_RE = re.compile(
    r"\b(?:afhentningskode|hentekode|udleveringskode|pickup\s*code|pick-up\s*code)\b"
    r"\s*(?:er|:|#|-)?\s*([A-Z0-9]{3,12})\b",
    re.IGNORECASE,
)
POSTNORD_PICKUP_LINK_RE = re.compile(r"https?://l\.postnord\.com/[^\s<>'\"]+", re.IGNORECASE)
POSTNORD_PICKUP_PAGE_NUMBER_RE = re.compile(
    r"\bpakkenummer\s*((?:\d[\s-]?){8,24})\b",
    re.IGNORECASE,
)
POSTNORD_PINCODE_RE = re.compile(
    r"\bpinkoden?\s+(\d{4,12})\b",
    re.IGNORECASE,
)
DAO_DELIVERED_EVENT_TEXT = "Pakken er udleveret"
DAO_PAKKENR_RE = re.compile(r"\bpakkenr\.?\s*:?\s*(\d{8,24})\b", re.IGNORECASE)
BRING_TRACKING_URL_RE = re.compile(
    r"https?://(?:www\.)?bring\.dk/t/(\d{8,24})\b",
    re.IGNORECASE,
)
GLS_TRACK_LINK_RE = re.compile(
    r"https?://[^\s<>\"']*?gls[^\s<>\"']*?[?&](?:match|txtRefNo)=([A-Z0-9][A-Z0-9-]{5,30})",
    re.IGNORECASE,
)
GLS_PAKKENUMMER_RE = re.compile(
    r"(?:dit\s+pakkenummer\s+er|gls\s+pakkenummer\s*:)\s*((?:\d[\s-]?){8,24})\b",
    re.IGNORECASE,
)
POSTNORD_PAKKE_RE = re.compile(r"\bdin\s+pakke\s+(\d{8,24})\s+fra\b", re.IGNORECASE)
FEDEX_TRACKING_ID_RE = re.compile(
    r"\btracking[-\s]?id\b\s*:?\s*(\d{12}|\d{15}|\d{20})\b",
    re.IGNORECASE,
)
FEDEX_SUBJECT_NUMBER_RE = re.compile(
    r"\bleveringsinstruktioner\s+(\d{12}|\d{15}|\d{20})\b",
    re.IGNORECASE,
)
FEDEX_DELIVERY_INSTRUCTION_RE = re.compile(
    r"\bleveringsinstruktioner\s+for\s+din\s+forsendelse\b",
    re.IGNORECASE,
)
POSTNORD_PICKUP_QR_RE = re.compile(
    r"\bqr[-\s]?kode\b[^0-9]{0,80}?(\d{2}(?:[\s-]\d{2}){2,5})\b",
    re.IGNORECASE | re.DOTALL,
)

NUMERIC_LENGTHS = {8, 9, 10, 11, 12, 13, 14, 15, 17, 18, 20, 22, 24}

CARRIER_KEYWORDS = {
    "DAO": {"dao", "dao.as", "daohome", "daoshop", "stregkode", "e-label"},
    "PostNord": {"postnord", "post nord"},
    "Bring": {"bring", "bring.dk", "bring.no", "posten bring"},
    "GLS": {"gls", "gls-group", "gls denmark"},
    "FedEx": {"fedex", "fedex.com", "fedex.dk"},
}


def normalize_gls_reference(value):
    cleaned = re.sub(r"[^0-9A-Z]+", "", str(value or "").upper())
    if len(cleaned) < 6 or len(cleaned) > 24:
        return None
    if not re.search(r"[A-Z]", cleaned):
        return None
    return cleaned


def _plain_text(value):
    text = unicodedata.normalize("NFC", html.unescape(str(value or "")))
    text = re.sub(r"<[^>]+>", " ", text)
    return re.sub(r"[ \t\r\f\v]+", " ", text)


def _norm_status_text(value):
    return re.sub(r"\s+", " ", str(value or "").strip()).lower()


def classify_shipment_status(carrier="", status="", status_code="", last_event_text=""):
    text = _norm_status_text(last_event_text)
    status_text = _norm_status_text(status)
    code = _norm_status_text(status_code)
    carrier_name = str(carrier or "").upper()

    if carrier_name in {"DAO", "GLS"} and "udleveret" in text:
        return "delivered"

    ready_markers = (
        "pakkeshop",
        "pakke shop",
        "pakke shoppen",
        "klar til afhentning",
        "ankommet til",
        "arrived at parcelshop",
    )
    if any(marker in text for marker in ready_markers):
        return "ready"

    delivered_markers = (
        "afhentet",
        "udleveret til modtager",
        "leveret hos modtager",
        "delivered to receiver",
    )
    if any(marker in text for marker in delivered_markers) or ("delivered" in code and "parcelshop" not in code):
        return "delivered"

    if any(marker in status_text for marker in delivered_markers):
        return "delivered"
    if any(marker in status_text for marker in ready_markers):
        return "ready"

    return "in_transit"


def normalize_tracking_number(value):
    return re.sub(r"[\s-]+", "", value or "").upper()


def normalize_pickup_code(value):
    cleaned = re.sub(r"[^0-9A-Z]+", "", str(value or "").upper())
    if not 3 <= len(cleaned) <= 12:
        return None
    if not re.search(r"\d", cleaned):
        return None
    return cleaned


def normalize_pickup_location(value):
    location = _clean_mail_label(value)
    if not location:
        return None
    location = re.sub(r"\s*,\s*", ", ", location)
    return location[:180] or None


def extract_pickup_code(text, carrier=None):
    plain = _plain_text(text)
    for match in PICKUP_CODE_RE.finditer(plain):
        code = normalize_pickup_code(match.group(1))
        if code:
            return code
    return None


def extract_pickup_location(text, carrier=None):
    carrier_name = str(carrier or "").strip().lower()

    plain = _plain_text(text)
    patterns = [
        r"\bhentested\s*:\s*(.+?)(?=\s+(?:hentekode|sporingsnummer)\s*:|\n\s*(?:hentekode|sporingsnummer)\s*:|$)",
        r"\ber\s+klar\s+til\s+afhentning\s+i\s+pakkeshop\s+(.+?)(?=\.\s*(?:hent\s+senest|vis\s+din\s+hentekode|hold\s+nemt)\b|\n|$)",
        r"\bklar\s+til\s+at\s+blive\s+hentet\s+i\s+(.+?)(?=\.\s|\n|$)",
        r"\bklar\s+til\s+afhentning\s+hos\s*:\s*(.+?)(?=\s+(?:åbningstider|aabningstider|brug\s+afhentningskode|pakken\s+skal)\b|$)",
        r"\bpakkeshoppen\s+hos\s*:\s*(.+?)(?=\s+(?:dit\s+pakkenummer|når\s+du\s+henter|du\s+kan\s+hente|tak,)\b|$)",
    ]
    for pattern in patterns:
        match = re.search(pattern, plain, flags=re.IGNORECASE | re.DOTALL)
        if match:
            location = normalize_pickup_location(match.group(1))
            if location:
                return location
    return None


def extract_gls_mail_label(text):
    plain = _plain_text(text)
    patterns = [
        r"din\s+pakke\s+fra\s+(.+?)\s+er\s+blevet\s+leveret\b",
        r"din\s+pakke\s+fra\s+(.+?)\s+er\s+afsendt\b",
        r"tak\s+fordi\s+du\s+handlede\s+hos\s+(.+?)(?:\s+din\s+pakke\b|\n|$)",
    ]
    match = None
    for pattern in patterns:
        match = re.search(pattern, plain, flags=re.IGNORECASE | re.DOTALL)
        if match:
            break
    if not match:
        return None

    return _clean_mail_label(match.group(1))


def _clean_mail_label(value):
    label = unicodedata.normalize("NFC", str(value or ""))
    label = re.sub(r"[\u200b\u200c\u200d\ufeff]+", "", label)
    label = re.sub(r"\s+", " ", label)
    label = re.sub(r"^[\s.,:;-]+|[\s.,:;-]+$", "", label)
    return label[:120] or None


def extract_dao_mail_label(text):
    plain = _plain_text(text)
    patterns = [
        r"(?:^|\n)\s*([^\n.]{2,120}?)\s+har\s+netop\s+indleveret\s+en\s+pakke\b",
        r"\bdin\s+pakke\s+\d{8,24}\s+fra\s+(.+?)\s+er\s+klar\s+til\s+afhentning\b",
    ]
    for pattern in patterns:
        match = re.search(pattern, plain, flags=re.IGNORECASE)
        if match:
            return _clean_mail_label(match.group(1))
    return None


def extract_bring_mail_label(text):
    plain = _plain_text(text)
    patterns = [
        r"din\s+pakke\s+fra\s+(.+?)\s+er\s+snart\b",
        r"din\s+pakke\s+fra\s+(.+?)\s+er\s+p[åa]\s+vej\b",
        r"\bdin\s+pakke\s+\d{8,24}\s+fra\s+(.+?)\s+kan\s+nu\s+hentes\b",
        r"\bfrom\s+(.+?)(?:\.dk)?\s+the\s+parcel\b",
    ]
    for pattern in patterns:
        match = re.search(pattern, plain, flags=re.IGNORECASE | re.DOTALL)
        if match:
            return _clean_mail_label(match.group(1))
    return None


def extract_postnord_mail_label(text):
    plain = _plain_text(text)
    patterns = [
        r"\b(?:vi\s+har\s+modtaget\s+)?din\s+pakke\s+\d{8,24}\s+fra\s+(.+?)\s+som\s+har\s+sendt\b",
        r"\bdin\s+pakke\s+fra\s+(.+?)\s+er\s+klar\s+til\s+afhentning\b",
        r"\bdin\s+pakke\s+fra\s+(.+?)\s+er\s+p[åa]\s+vej\b",
    ]
    for pattern in patterns:
        match = re.search(pattern, plain, flags=re.IGNORECASE | re.DOTALL)
        if match:
            return _clean_mail_label(match.group(1))
    return None


def is_postnord_ready_mail(text):
    plain = _plain_text(text)
    return bool(
        re.search(r"\bdin\s+postnord-pakke\s+er\s+klar\s+til\s+afhentning\b", plain, flags=re.IGNORECASE)
        or re.search(
            r"\bdin\s+pakke\s+fra\s+.+?\s+er\s+klar\s+til\s+afhentning\s+i\s+pakkeshop\b",
            plain,
            flags=re.IGNORECASE | re.DOTALL,
        )
    )


def is_gls_ready_mail(text):
    plain = _plain_text(text)
    has_intro = re.search(
        r"\bnu\s+kan\s+du\s+godt\s+begynde\s+at\s+(?:glæde|glaede)\s+dig\.\s+din\s+pakke\s+fra\b",
        plain,
        flags=re.IGNORECASE,
    )
    has_delivery = re.search(
        r"\ber\s+blevet\s+leveret\s+af\s+din\s+lokale\s+gls-?chauff(?:ør|oer)\b",
        plain,
        flags=re.IGNORECASE,
    )
    return bool(has_intro and has_delivery)


def extract_dao_mail_event_text(text):
    plain = _plain_text(text)
    if re.search(r"\bpakken\s+er\s+udleveret\b", plain, flags=re.IGNORECASE):
        return DAO_DELIVERED_EVENT_TEXT
    return None


def extract_dao_mail_tracking_numbers(text):
    plain = _plain_text(text)
    seen = set()
    results = []
    # "Afsendt" mails
    if re.search(r"\bhar\s+netop\s+indleveret\s+en\s+pakke\b", plain, re.IGNORECASE):
        for match in DAO_PAKKENR_RE.finditer(plain):
            number = normalize_tracking_number(match.group(1))
            if number and number not in seen:
                seen.add(number)
                results.append(number)
        return results
    # "Klar til afhentning" mails: "din pakke {number} fra X er klar til afhentning"
    for match in re.finditer(
        r"\bdin\s+pakke\s+(\d{8,24})\s+fra\b.{0,120}?\ber\s+klar\s+til\s+afhentning\b",
        plain, re.IGNORECASE | re.DOTALL,
    ):
        number = normalize_tracking_number(match.group(1))
        if number and number not in seen:
            seen.add(number)
            results.append(number)
    if results:
        return results
    # "Udleveret" mails: "Pakken er udleveret" + Pakkenr.
    if re.search(r"\bpakken\s+er\s+udleveret\b", plain, re.IGNORECASE):
        for match in DAO_PAKKENR_RE.finditer(plain):
            number = normalize_tracking_number(match.group(1))
            if number and number not in seen:
                seen.add(number)
                results.append(number)
    return results


def extract_bring_mail_tracking_numbers(text):
    plain = _plain_text(text)
    if not (
        re.search(r"\bbring\b", plain, re.IGNORECASE)
        and re.search(r"\bdin\s+pakke\s+fra\b", plain, re.IGNORECASE)
    ):
        return []
    raw = html.unescape(str(text or ""))
    seen = set()
    results = []
    for match in BRING_TRACKING_URL_RE.finditer(raw):
        number = normalize_tracking_number(match.group(1))
        if number and number not in seen:
            seen.add(number)
            results.append(number)

    if not results:
        for match in re.finditer(r"\b(3\d{17}|7\d{16})\b", plain):
            number = normalize_tracking_number(match.group(1))
            if number and number not in seen:
                seen.add(number)
                results.append(number)
    return results


def extract_gls_mail_tracking_numbers(text):
    plain = _plain_text(text)
    if is_gls_ready_mail(plain):
        seen = set()
        results = []
        for match in GLS_PAKKENUMMER_RE.finditer(plain):
            number = normalize_tracking_number(match.group(1))
            if not (number.isdigit() and 10 <= len(number) <= 14):
                continue
            if number not in seen:
                seen.add(number)
                results.append(number)
        return results

    if not (
        re.search(r"\btak\s+fordi\s+du\s+handlede\s+hos\b", plain, re.IGNORECASE)
        and re.search(r"\bafsendt\s+med\s+GLS\b", plain, re.IGNORECASE)
    ):
        return []
    raw = html.unescape(str(text or ""))
    seen = set()
    results = []
    for match in GLS_TRACK_LINK_RE.finditer(raw):
        reference = normalize_gls_reference(match.group(1))
        if reference and reference not in seen:
            seen.add(reference)
            results.append(reference)
    return results


def extract_postnord_mail_tracking_numbers(text):
    plain = _plain_text(text)
    if not re.search(r"\bpostnord[.-]pakke\b", plain, re.IGNORECASE):
        return []
    seen = set()
    results = []
    for match in POSTNORD_PAKKE_RE.finditer(plain):
        number = normalize_tracking_number(match.group(1))
        if number and number not in seen:
            seen.add(number)
            results.append(number)
    return results


def extract_fedex_mail_tracking_numbers(text):
    plain = _plain_text(text)
    is_fedex_service_mail = bool(re.search(r"\bfedex\b", plain, re.IGNORECASE))
    is_delivery_instruction_mail = bool(FEDEX_DELIVERY_INSTRUCTION_RE.search(plain))
    if not (is_fedex_service_mail and is_delivery_instruction_mail):
        return []
    seen = set()
    results = []
    # "Tracking-id: 872463189276" (service/tjeneste email)
    for match in FEDEX_TRACKING_ID_RE.finditer(plain):
        number = normalize_tracking_number(match.group(1))
        if number and number not in seen:
            seen.add(number)
            results.append(number)
    # Subject: "...leveringsinstruktioner 872463189276" (first delivery instruction email)
    if not results:
        for match in FEDEX_SUBJECT_NUMBER_RE.finditer(plain):
            number = normalize_tracking_number(match.group(1))
            if number and number not in seen:
                seen.add(number)
                results.append(number)
    return results


def extract_postnord_pickup_links(text):
    raw = html.unescape(str(text or ""))
    links = []
    seen = set()
    for match in POSTNORD_PICKUP_LINK_RE.finditer(raw):
        link = match.group(0).rstrip(".,;:)]}")
        if link and link not in seen:
            seen.add(link)
            links.append(link)
    return links


def extract_postnord_pickup_page_details(text):
    plain = _plain_text(text)
    number_match = POSTNORD_PICKUP_PAGE_NUMBER_RE.search(plain)
    tracking_number = normalize_tracking_number(number_match.group(1)) if number_match else None
    pickup_code = extract_postnord_pincode(plain)
    if not pickup_code:
        qr_match = POSTNORD_PICKUP_QR_RE.search(plain)
        if qr_match:
            pickup_code = normalize_pickup_code(qr_match.group(1))
    return {
        "tracking_number": tracking_number,
        "pickup_code": pickup_code,
    }


def extract_postnord_pincode(text):
    plain = _plain_text(text)
    match = POSTNORD_PINCODE_RE.search(plain)
    if not match:
        return None
    return normalize_pickup_code(match.group(1))


def extract_mail_label(carrier, text):
    carrier_name = str(carrier or "").strip().lower()
    if carrier_name == "gls":
        return extract_gls_mail_label(text)
    if carrier_name == "dao":
        return extract_dao_mail_label(text)
    if carrier_name == "bring":
        return extract_bring_mail_label(text)
    if carrier_name == "postnord":
        return extract_postnord_mail_label(text)
    return None


def extract_gls_reference_numbers(text):
    raw = html.unescape(str(text or ""))
    patterns = [
        r"(?:[?&;]|\b)txtRefNo\s*=\s*([A-Z0-9%+-]{6,40})",
        r"\b(?:ref\.?\s*nr\.?|pakkenr\.?)\s*[:#]?\s*([A-Z0-9][A-Z0-9 -]{5,30})",
    ]
    references = []
    seen = set()
    for pattern in patterns:
        for match in re.finditer(pattern, raw, flags=re.IGNORECASE):
            reference = normalize_gls_reference(unquote_plus(match.group(1)))
            if reference and reference not in seen:
                seen.add(reference)
                references.append(reference)
    return references


def gls_alias_key(tracking_number):
    number = normalize_tracking_number(tracking_number)
    if not number.isdigit():
        return None

    if len(number) == 10 and not number.startswith("0"):
        return number
    if len(number) == 11 and number.startswith("0"):
        return number[1:]
    if len(number) == 12 and number.startswith("0"):
        return number[1:-1]
    return None


def gls_alias_preference(tracking_number):
    number = normalize_tracking_number(tracking_number)
    if len(number) == 12 and number.startswith("0"):
        return 3
    if len(number) == 11 and number.startswith("0"):
        return 2
    if len(number) == 10 and not number.startswith("0"):
        return 1
    return 0


def has_tracking_context(text):
    lowered = (text or "").lower()
    return any(keyword in lowered for keyword in CONTEXT_KEYWORDS)


def _context_carriers(text):
    lowered = (text or "").lower()
    return [
        carrier
        for carrier, keywords in CARRIER_KEYWORDS.items()
        if any(keyword in lowered for keyword in keywords)
    ]


def _is_s10(number):
    return bool(re.fullmatch(r"[A-Z]{2}\d{9}[A-Z]{2}", number))


def _is_valid_for_carrier(number, carrier):
    if not number:
        return False

    if carrier == "DAO":
        return number.isdigit() and (
            len(number) == 9
            or (len(number) == 13 and number.startswith("7"))
            or (len(number) == 20 and number.startswith("00057"))
        )

    if carrier == "PostNord":
        return _is_s10(number) or (number.isdigit() and len(number) in {13, 14, 18, 20})

    if carrier == "Bring":
        return _is_s10(number) or (
            number.isdigit()
            and ((len(number) == 18 and number.startswith("3")) or (len(number) == 17 and number.startswith("7")))
        )

    if carrier == "GLS":
        return number.isdigit() and 8 <= len(number) <= 14

    return False


def detect_carrier(tracking_number, context=""):
    number = normalize_tracking_number(tracking_number)
    lowered = (context or "").lower()
    context_carriers = _context_carriers(context)

    if number.startswith("1Z") and len(number) == 18:
        return "UPS"
    if number.isdigit() and len(number) == 20 and number.startswith("00057"):
        return "DAO"

    for carrier in context_carriers:
        if _is_valid_for_carrier(number, carrier):
            return carrier

    if "postnord" in lowered or "post nord" in lowered:
        return "PostNord"
    if "gls" in lowered:
        return "GLS"
    if "dhl" in lowered:
        return "DHL"
    if "fedex" in lowered:
        return "FedEx"
    if "bring" in lowered:
        return "Bring"
    if "dao" in lowered:
        return "DAO"
    if "instabox" in lowered:
        return "Instabox"
    if "budbee" in lowered:
        return "Budbee"

    if _is_s10(number):
        if number.endswith(("DK", "SE", "NO", "FI")):
            return "PostNord"
        return "International Post"
    if number.isdigit() and len(number) in {12, 15, 20, 22}:
        return "FedEx"
    if number.isdigit() and len(number) == 10:
        return "DHL"
    return "Unknown"


def build_tracking_url(tracking_number, carrier=None):
    number = normalize_tracking_number(tracking_number)
    encoded = quote_plus(number)
    carrier_name = carrier or detect_carrier(number)

    urls = {
        "DAO": f"https://dao.as/find-din-pakke/#q={encoded}",
        "PostNord": f"https://www.postnord.dk/varktojer/track-trace?shipmentId={encoded}",
        "Bring": f"https://tracking.bring.com/tracking/{encoded}",
        "GLS": f"https://gls-group.com/DK/da/find-pakke?match={encoded}",
        "UPS": f"https://www.ups.com/track?tracknum={encoded}",
        "DHL": f"https://www.dhl.com/global-en/home/tracking.html?tracking-id={encoded}",
        "FedEx": f"https://www.fedex.com/fedextrack/?trknbr={encoded}",
    }
    return urls.get(carrier_name, f"https://t.17track.net/en#nums={encoded}")


def _candidate_numbers(text):
    candidates = []

    for regex in (URL_VALUE_RE, LABEL_VALUE_RE):
        for match in regex.finditer(text or ""):
            number = normalize_tracking_number(match.group(1))
            if number:
                candidates.append((number, True))

    for regex in (UPS_RE, S10_RE, NUMERIC_RE, ALNUM_TOKEN_RE):
        for match in regex.finditer(text or ""):
            raw = match.group(0)
            number = normalize_tracking_number(raw)
            if not number:
                continue
            if number.isdigit() and len(number) not in NUMERIC_LENGTHS:
                continue
            if number.isalpha():
                continue
            candidates.append((number, False))

    return _remove_partial_candidates(candidates)


def _remove_partial_candidates(candidates):
    merged = {}
    for number, anchored in candidates:
        merged[number] = merged.get(number, False) or anchored

    numbers = list(merged.keys())
    filtered = []
    for number in numbers:
        if any(number != other and number in other and len(other) > len(number) for other in numbers):
            continue
        filtered.append((number, merged[number]))

    return filtered


def _is_strong_free_candidate(number, carrier):
    if number.startswith("1Z") and len(number) == 18:
        return True
    if _is_s10(number):
        return True
    if carrier == "DAO" and number.isdigit() and len(number) == 20 and number.startswith("00057"):
        return True
    if carrier == "Bring" and number.isdigit() and (
        (len(number) == 18 and number.startswith("3")) or (len(number) == 17 and number.startswith("7"))
    ):
        return True
    if carrier == "PostNord" and (number.isdigit() and len(number) in {13, 14, 18, 20}):
        return True
    return False


def _carrier_for_candidate(number, context, anchored=False):
    context_carriers = _context_carriers(context)
    for carrier in context_carriers:
        if _is_valid_for_carrier(number, carrier) and (anchored or _is_strong_free_candidate(number, carrier)):
            return carrier

    if context_carriers:
        return None

    detected = detect_carrier(number, context)
    if detected in SUPPORTED_SCAN_CARRIERS and not _is_valid_for_carrier(number, detected):
        return None
    if detected != "Unknown":
        return detected
    return None


def extract_tracking_numbers(text):
    context_ok = has_tracking_context(text)
    seen = set()
    results = []

    for number, anchored in _candidate_numbers(text or ""):
        strong_pattern = number.startswith("1Z") or _is_s10(number)
        if not strong_pattern and not context_ok:
            continue
        if number in seen:
            continue

        carrier = _carrier_for_candidate(number, text, anchored)
        if not carrier:
            continue

        seen.add(number)
        results.append(
            {
                "tracking_number": number,
                "carrier": carrier,
                "tracking_url": build_tracking_url(number, carrier),
            }
        )

    return results
