import os


BASE_URL = "https://127.0.0.1"
CS2_API_URL = f"{BASE_URL}/api/v1"
KEYCLOAK_URL = f"{BASE_URL}/auth"

USE_AUTH = True

# If SSL certificate is not available in the operating system trust store, set
# this environement variable. Otherwise it can be left unset (or explicitly set
# None here).
CERT_PATH = os.environ.get("CERT_PATH")

KEYCLOAK_CLIENT_ID = "cs2_api_example"
KEYCLOAK_REALM = "cs2"
KEYCLOAK_CLIENT_SECRET = os.environ["CS2_CLIENT_SECRET"]


service_booster_pump_available = False
number_of_circulation_turbo_pumps = 1  # Configured B1 circulation turbo pumps (1-3), sets the still heater power in condensing
