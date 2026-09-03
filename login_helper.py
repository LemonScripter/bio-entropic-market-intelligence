"""
Interactive Amazon Session Authenticator.
Opens a visible browser window allowing the user to sign in to Amazon.
Upon successful authentication, saves the storage state to data/sessions/session_state.json.
"""

import sys
import asyncio
from pathlib import Path
from playwright.async_api import async_playwright

SESSION_PATH = Path("data/sessions/session_state.json")
SESSION_PATH.parent.mkdir(parents=True, exist_ok=True)

async def interactive_login():
    print("=" * 60)
    print("      AMAZON INTERAKTIV BEJELENTKEZESI SEGED")
    print("=" * 60)
    print("\n1. Megnyilik egy lathato bongeszo ablak.")
    print("2. Jelentkezz be a sajat Amazon fiokoddal.")
    print("3. Amint beleptel, a rendszer automatikusan elmenti a munkamenetet!\n")

    async with async_playwright() as p:
        # Launch visible browser
        browser = await p.chromium.launch(
            headless=False,
            args=[
                "--disable-blink-features=AutomationControlled",
                "--start-maximized"
            ]
        )
        context = await browser.new_context(
            viewport=None,
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
        )
        page = await context.new_page()

        login_url = "https://www.amazon.com/ap/signin?openid.pape.max_auth_age=3600&openid.return_to=https%3A%2F%2Fwww.amazon.com%2F%3Fref_%3Dnav_custrec_signin&openid.identity=http%3A%2F%2Fspecs.openid.net%2Fauth%2F2.0%2Fidentifier_select&openid.assoc_handle=usflex&openid.mode=checkid_setup&openid.claimed_id=http%3A%2F%2Fspecs.openid.net%2Fauth%2F2.0%2Fidentifier_select&openid.ns=http%3A%2F%2Fspecs.openid.net%2Fauth%2F2.0"
        
        await page.goto(login_url)
        print("-> Varakozas a sikeres bejelentkezesre...")

        # Poll until user is logged in
        while True:
            await asyncio.sleep(2)
            try:
                # Check if landed on home page or account name appears
                url = page.url
                content = await page.content()
                
                # If navigated away from signin/ap/ and not on captcha
                if ("amazon.com" in url) and ("ap/signin" not in url) and ("openid" not in url):
                    # Check for sign out link or logged in greetings
                    if ("nav-item-signout" in content) or ("Hello, " in content) or ("nav-link-accountList" in content and "Sign in" not in content):
                        print("\n[SIKER] Bejelentkezes eszlelve!")
                        await asyncio.sleep(2) # let remaining cookies settle
                        await context.storage_state(path=str(SESSION_PATH))
                        print(f"[OK] Hitelesitett munkamenet elmentve ide: {SESSION_PATH.resolve()}")
                        break
            except Exception:
                pass

        await browser.close()
        print("\nKesz! A session mostantol aktiv a melyrehato lapozashoz.")

if __name__ == "__main__":
    asyncio.run(interactive_login())
