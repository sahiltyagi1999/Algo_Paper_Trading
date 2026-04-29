"""
Zerodha Login Helper
Run this once every morning before starting the algo.
It opens the browser, you login, paste the request token, and it saves the access token.
"""

import os
import webbrowser
from kiteconnect import KiteConnect
import config

TOKEN_FILE = config.TOKEN_FILE


def get_kite():
    """Return authenticated KiteConnect instance."""
    kite = KiteConnect(api_key=config.API_KEY)

    # If token saved today, reuse it
    if os.path.exists(TOKEN_FILE):
        with open(TOKEN_FILE) as f:
            lines = f.read().strip().splitlines()
        if len(lines) == 2:
            saved_date, token = lines
            from datetime import date
            if saved_date == str(date.today()):
                kite.set_access_token(token)
                print("✓ Reusing today's access token.")
                return kite

    # Fresh login
    login_url = kite.login_url()
    print("\n" + "="*55)
    print("  ZERODHA LOGIN REQUIRED")
    print("="*55)
    print(f"  1. Browser will open: {login_url}")
    print("  2. Login with your Zerodha credentials")
    print("  3. After login, copy the 'request_token' from the URL")
    print("     URL looks like: ?request_token=XXXXXXXX&action=login")
    print("="*55 + "\n")

    webbrowser.open(login_url)
    request_token = input("Paste request_token here: ").strip()

    data = kite.generate_session(request_token, api_secret=config.API_SECRET)
    access_token = data["access_token"]
    kite.set_access_token(access_token)

    # Save token with today's date
    os.makedirs(os.path.dirname(TOKEN_FILE), exist_ok=True)
    from datetime import date
    with open(TOKEN_FILE, "w") as f:
        f.write(f"{date.today()}\n{access_token}")

    print("✓ Login successful! Access token saved.")
    return kite


if __name__ == "__main__":
    kite = get_kite()
    profile = kite.profile()
    print(f"\nLogged in as: {profile['user_name']} ({profile['user_id']})")
