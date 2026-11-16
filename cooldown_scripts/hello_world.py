"""HTTP API example for Control Software 2

Reads the P6 pressure, then opens valve V104 and closes it again.

Before running the script set the automation to Manual operation
from the CS2 dashboard, and make sure V104 can safely be opened.

Note: if CS2 uses authentication, follow the instructions described
in KEYCLOAK_API_CLIENT.md to setup the keycloak client
"""

import json
import os
import ssl
import time
import uuid
from urllib import parse, request


# --- Settings ---

BASE_URL = "https://127.0.0.1"
CS2_API_URL = f"{BASE_URL}/api/v1"

# Keycloak authentication. Set USE_AUTH to False if the CS2 instance runs
# without Keycloak; the secret is then optional.
USE_AUTH = True
KEYCLOAK_URL = f"{BASE_URL}/auth"
KEYCLOAK_REALM = "cs2"
KEYCLOAK_CLIENT_ID = "cs2_api_example"

# Create the client as described in KEYCLOAK_API_CLIENT.md, then export its secret
# before running the script:
#   PowerShell: $env:CS2_CLIENT_SECRET = "the-secret-from-keycloak"
#   bash/zsh:   export CS2_CLIENT_SECRET="the-secret-from-keycloak"
KEYCLOAK_CLIENT_SECRET = os.environ.get("CS2_CLIENT_SECRET")

# Optional: a certificate to trust in addition to the system trust store, for
# when the CS2 certificate is not installed on this machine (see the SSL/TLS
# section of the top-level README).
CERT_PATH = os.environ.get("CERT_PATH")

PRESSURE = "P6_PRESSURE"
VALVE = "V104"


ssl_context = ssl.create_default_context()
if CERT_PATH:
    ssl_context.load_verify_locations(cafile=CERT_PATH)


def get_token():
    # The token is valid for a few minutes, which is enough for this script.
    # Longer-running scripts must fetch a new one before it expires.
    data = parse.urlencode(
        {
            "grant_type": "client_credentials",
            "client_id": KEYCLOAK_CLIENT_ID,
            "client_secret": KEYCLOAK_CLIENT_SECRET,
            "scope": "openid",
        }
    ).encode("utf-8")
    url = f"{KEYCLOAK_URL}/realms/{KEYCLOAK_REALM}/protocol/openid-connect/token"
    with request.urlopen(request.Request(url, data=data, method="POST"), context=ssl_context) as res:
        return json.load(res)["access_token"]


def get(path, headers):
    req = request.Request(f"{CS2_API_URL}{path}", headers=headers)
    with request.urlopen(req, context=ssl_context) as res:
        return json.load(res)


def post(path, headers, body):
    req = request.Request(
        f"{CS2_API_URL}{path}",
        data=json.dumps(body).encode("utf-8"),
        headers={**headers, "Content-Type": "application/json"},
        method="POST",
    )
    with request.urlopen(req, context=ssl_context) as res:
        return json.load(res)


def set_valve(headers, valve, open_valve):
    command = {
        "commandId": "command",
        "correlationId": str(uuid.uuid4()),
        "payload": {"valveOnOff": open_valve},
    }
    return post(f"/devices/{valve}/command", headers, command)


def main():
    headers = {}
    if USE_AUTH:
        if not KEYCLOAK_CLIENT_SECRET:
            raise SystemExit(
                "CS2_CLIENT_SECRET is not set. Export the client secret from "
                "Keycloak (see KEYCLOAK_API_CLIENT.md), or set USE_AUTH = False."
            )
        print("Fetching access token from Keycloak...")
        headers["Authorization"] = f"Bearer {get_token()}"
        print("Access token obtained.")
    else:
        print("Authentication is disabled.")

    print(f"Reading pressure {PRESSURE}...")
    pressure = get(f"/state/devices?keys={parse.quote(PRESSURE)}", headers)[PRESSURE]
    print(f"{PRESSURE} = {pressure} bar")

    print(f"Sending open command to {VALVE}...")
    print("Response:", set_valve(headers, VALVE, True))
    print(f"Waiting 5 seconds with {VALVE} open...")
    time.sleep(5)

    print(f"Sending close command to {VALVE}...")
    print("Response:", set_valve(headers, VALVE, False))
    print("Done.")


if __name__ == "__main__":
    main()
