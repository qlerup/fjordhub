"""
Åbn en synlig browser, log ind på 17TRACK og løs CAPTCHA'en.
Sign-cookien gemmes automatisk i .17track_profile/ og TRACK17_SIGN opdateres i .env.

Kør: python scripts/refresh_sign.py
"""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).parent.parent
BROWSER_PROFILE_DIR = ROOT / ".17track_profile"
ENV_PATH = ROOT / ".env"
TEST_NUMBER = "00073215400595127740"


def save_sign(sign: str) -> None:
    if not ENV_PATH.exists():
        print(f"Advarsel: .env ikke fundet – gemmer ikke sign automatisk.")
        print(f"Tilføj manuelt: TRACK17_SIGN={sign}")
        return
    content = ENV_PATH.read_text(encoding="utf-8")
    if "TRACK17_SIGN" in content:
        content = re.sub(r"^TRACK17_SIGN=.*$", f"TRACK17_SIGN={sign}", content, flags=re.MULTILINE)
    else:
        content = content.rstrip("\n") + f"\nTRACK17_SIGN={sign}\n"
    ENV_PATH.write_text(content, encoding="utf-8")
    print(f"Sign gemt i .env (længde: {len(sign)} tegn).")


def main() -> None:
    try:
        from playwright.sync_api import sync_playwright
    except ImportError:
        print("Fejl: playwright er ikke installeret.")
        print("Kør: pip install playwright && playwright install chromium")
        sys.exit(1)

    BROWSER_PROFILE_DIR.mkdir(parents=True, exist_ok=True)

    print("Åbner browser – løs CAPTCHA'en og vent på at tracking-data vises.")
    print("Luk IKKE browseren manuelt – scriptet lukker den automatisk.\n")

    new_sign: list[str] = []
    got_data = False

    with sync_playwright() as p:
        ctx = p.chromium.launch_persistent_context(
            str(BROWSER_PROFILE_DIR),
            headless=False,
            user_agent=(
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/125.0.0.0 Safari/537.36"
            ),
            locale="da-DK",
            viewport={"width": 1280, "height": 900},
        )

        def on_response(response: object) -> None:
            nonlocal got_data
            if "restapi" in response.url and response.status == 200:  # type: ignore[attr-defined]
                try:
                    data = json.loads(response.text())  # type: ignore[attr-defined]
                    if int((data.get("meta") or {}).get("code") or 0) == 200:
                        got_data = True
                        try:
                            req_body = json.loads(response.request.post_data or "{}")  # type: ignore[attr-defined]
                            sign = str(req_body.get("sign") or "")
                            if sign and not new_sign:
                                new_sign.append(sign)
                                print(f"\nSign fanget fra succesfuld request (længde: {len(sign)} tegn).")
                        except Exception:
                            pass
                        print("Tracking-data modtaget – lukker browser...")
                except Exception:
                    pass

        page = ctx.new_page()
        page.on("response", on_response)

        page.goto(
            f"https://t.17track.net/en#nums={TEST_NUMBER}",
            wait_until="domcontentloaded",
        )

        print(f"Browser åbnet: https://t.17track.net/en#nums={TEST_NUMBER}")
        print("Acceptér cookies og løs CAPTCHA'en i browservinduet...")

        page.wait_for_function(
            "() => window.__trackDone === true",
            timeout=0,
            polling=500,
        ) if False else None

        deadline = 120
        print(f"Venter op til {deadline} sekunder på tracking-data...")
        for _ in range(deadline * 2):
            page.wait_for_timeout(500)
            if got_data:
                break

        if not got_data and not new_sign:
            print("\nVentede uden resultat – prøv igen.")
            ctx.close()
            sys.exit(1)

        ctx.close()

    if new_sign:
        save_sign(new_sign[0])
        print("\n" + "=" * 60)
        print("KOPIER SIGN'ET NEDENFOR OG INDSÆT I APPEN (Indstillinger → Fragtfirmaer → PostNord):")
        print("=" * 60)
        print(new_sign[0])
        print("=" * 60)
        print("\nFærdig! Sign'et virker i ~1 år.")
    else:
        print("\nSign ikke fanget – prøv igen.")
        sys.exit(1)


if __name__ == "__main__":
    main()
