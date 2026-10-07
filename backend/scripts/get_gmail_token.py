"""Skrypt pomocniczy do wygenerowania GMAIL_REFRESH_TOKEN dla PhysioCare.

Użycie:
    python backend/scripts/get_gmail_token.py
"""

import http.server
import json
import socketserver
import sys
import urllib.parse
import webbrowser

import requests

PORT = 8080
REDIRECT_URI = f"http://localhost:{PORT}/callback"
SCOPE = "https://www.googleapis.com/auth/gmail.send"


class OAuthCallbackHandler(http.server.BaseHTTPRequestHandler):
    auth_code = None

    def do_GET(self):
        parsed = urllib.parse.urlparse(self.path)
        params = urllib.parse.parse_qs(parsed.query)

        if "code" in params:
            OAuthCallbackHandler.auth_code = params["code"][0]
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.end_headers()
            self.wfile.write(
                """
                <html>
                <body style="font-family: sans-serif; text-align: center; padding-top: 50px;">
                    <h2 style="color: #059669;">Autoryzacja udana!</h2>
                    <p>Możesz zamknąć to okno i wrócić do konsoli terminala.</p>
                </body>
                </html>
                """.encode()
            )
        elif "error" in params:
            error = params.get("error", ["unknown"])[0]
            self.send_response(400)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.end_headers()
            self.wfile.write(f"<h3>Blad autoryzacji: {error}</h3>".encode())
        else:
            self.send_response(404)
            self.end_headers()

    def log_message(self, format, *args):
        # Wyciszenie logów HTTP
        pass


def main():
    print("=" * 60)
    print(" PhysioCare - Generator GMAIL_REFRESH_TOKEN")
    print("=" * 60)
    print("\nZanim przejdziesz dalej, upewnij sie ze w Google Cloud Console:")
    print(" 1. Wlaczyles 'Gmail API' w projekcie.")
    print(" 2. W 'Authorized redirect URIs' dodales: http://localhost:8080/callback")
    print("=" * 60)

    client_id = input("\nPodaj Google CLIENT_ID: ").strip()
    if not client_id:
        print("Blad: CLIENT_ID nie moze byc puste.")
        sys.exit(1)

    client_secret = input("Podaj Google CLIENT_SECRET: ").strip()
    if not client_secret:
        print("Blad: CLIENT_SECRET nie moze byc puste.")
        sys.exit(1)

    auth_params = {
        "client_id": client_id,
        "redirect_uri": REDIRECT_URI,
        "response_type": "code",
        "scope": SCOPE,
        "access_type": "offline",
        "prompt": "consent",
    }
    auth_url = f"https://accounts.google.com/o/oauth2/v2/auth?{urllib.parse.urlencode(auth_params)}"

    print("\nOtwieram przegladarke w celu autoryzacji konta Google...")
    print(f"Jesli sie nie otworzy automatycznie, przejdz pod ten adres:\n{auth_url}\n")
    webbrowser.open(auth_url)

    print(f"Oczekiwanie na odpowiedz Google na http://localhost:{PORT}...")
    server = socketserver.TCPServer(("localhost", PORT), OAuthCallbackHandler)
    while OAuthCallbackHandler.auth_code is None:
        server.handle_request()
    server.server_close()

    code = OAuthCallbackHandler.auth_code
    print("Kod autoryzacyjny zostal odebrany! Wymieniam go na refresh_token...")

    token_url = "https://oauth2.googleapis.com/token"
    data = {
        "client_id": client_id,
        "client_secret": client_secret,
        "code": code,
        "grant_type": "authorization_code",
        "redirect_uri": REDIRECT_URI,
    }

    resp = requests.post(token_url, data=data, timeout=15)
    if not resp.ok:
        print(f"\nBlad wymiany kodu ({resp.status_code}): {resp.text}")
        sys.exit(1)

    tokens = resp.json()
    refresh_token = tokens.get("refresh_token")

    if not refresh_token:
        print("\nUwaga: Google nie zwrocilo 'refresh_token'.")
        print("Prawdopodobnie aplikacja byla juz wczesniej autoryzowana bez parametru prompt=consent.")
        print(f"Otrzymana odpowiedz:\n{json.dumps(tokens, indent=2)}")
        sys.exit(1)

    print("\n" + "=" * 60)
    print(" SUKCES! Otrzymano GMAIL_REFRESH_TOKEN:")
    print("=" * 60)
    print(f"\nGMAIL_REFRESH_TOKEN={refresh_token}")
    print("\nDodaj nastepujace zmienne srodowiskowe w panelu Render (Environment):")
    print("EMAIL_BACKEND=core.gmail_backend.GmailApiEmailBackend")
    print(f"GMAIL_CLIENT_ID={client_id}")
    print(f"GMAIL_CLIENT_SECRET={client_secret}")
    print(f"GMAIL_REFRESH_TOKEN={refresh_token}")
    print("=" * 60)


if __name__ == "__main__":
    main()
