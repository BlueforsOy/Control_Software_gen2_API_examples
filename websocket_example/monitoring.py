"""Subscribe to a CS2 WebSocket topic and log incoming messages.

A small script that subscribes to a CS2 WebSocket topic over STOMP and logs
incoming messages. It authenticates to Keycloak with the client-credentials
flow, opens a WebSocket connection to the CS2 server, subscribes to the
configured topics, and prints each message as it arrives. If the connection
drops, it reconnects with a fresh token and exponential backoff.

Run from the repo root:

    python -m websocket_example.monitoring
"""

import logging
import os
import threading

import stomp

from auth.keycloak import KeycloakAuthClient


# --- Configuration ---

HOST = "localhost"
PORT = 443
VHOST = "localhost"

# Set to point to certificate file if using self-signed certificate that is not
# found in the system certificate store
CERT_PATH = None

# Set to False if your CS2 instance is running without Keycloak.
USE_AUTH = True
KEYCLOAK_REALM = "cs2"
CLIENT_ID = "cs2_api_example"

# Get the secret from your Keycloak realm's client settings and export it:
#   export CS2_CLIENT_SECRET=...
CLIENT_SECRET = os.environ.get("CS2_CLIENT_SECRET")

# Topics to subscribe to: (subscription_id, destination)
SUBSCRIPTIONS = [
    ("sub-events-values", "/topic/events/values"),
]

RECONNECT_INITIAL_DELAY_S = 2
RECONNECT_MAX_DELAY_S = 60
HEARTBEAT_MS = (15000, 15000)


logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(message)s",
)
log = logging.getLogger(__name__)


class Subscriber(stomp.ConnectionListener):
    """Owns the STOMP connection and reconnects on drop."""

    def __init__(self, auth):
        self.auth = auth
        self.conn = None
        self._disconnected = threading.Event()
        self._shutdown = threading.Event()

    # Listener callbacks (run on stomp's receiver thread)

    def on_connected(self, frame):
        log.info("CONNECTED: %s", frame.headers)

    def on_message(self, frame):
        log.info("MESSAGE: %s", frame.body)

    def on_error(self, frame):
        log.error("ERROR: %s", frame.body)

    def on_disconnected(self):
        log.warning("DISCONNECTED")
        # Signal the main thread to reconnect — don't block this thread.
        self._disconnected.set()

    # Main-thread control

    def run(self):
        self._connect()
        while not self._shutdown.is_set():
            if self._disconnected.wait(timeout=1.0):
                self._disconnected.clear()
                if not self._shutdown.is_set():
                    self._reconnect_with_backoff()

    def shutdown(self):
        self._shutdown.set()
        if self.conn is not None:
            try:
                self.conn.disconnect()
            except Exception as e:
                log.warning("Clean disconnect failed: %s", e)

    def _connect(self):
        token = self.auth.get_auth_token() if self.auth else None
        headers = {"authorization": token} if token else {}

        conn = stomp.WSConnection(
            [(HOST, PORT)],
            ws_path="/socket/websocket",
            header=headers,
            vhost=VHOST,
            heartbeats=HEARTBEAT_MS,
        )
        if CERT_PATH:
            conn.set_ssl(for_hosts=[(HOST, PORT)], ca_certs=CERT_PATH)
        else:
            # picks up the certificates from system trust store
            conn.set_ssl(for_hosts=[(HOST, PORT)])
        conn.set_listener("", self)
        conn.connect(wait=True, with_connect_command=True, headers=headers)

        for sub_id, destination in SUBSCRIPTIONS:
            conn.subscribe(destination=destination, id=sub_id, ack="auto")
            log.info("Subscribed to %s (id=%s)", destination, sub_id)

        self.conn = conn

    def _reconnect_with_backoff(self):
        delay = RECONNECT_INITIAL_DELAY_S
        while not self._shutdown.is_set():
            log.info("Reconnecting in %ss...", delay)
            if self._shutdown.wait(timeout=delay):
                return
            try:
                self._connect()
                return
            except Exception as e:
                log.error("Reconnect failed: %s", e)
                delay = min(delay * 2, RECONNECT_MAX_DELAY_S)


def main():
    auth = None
    if USE_AUTH:
        if not CLIENT_SECRET:
            raise SystemExit(
                "CS2_CLIENT_SECRET is not set. Get the secret from your "
                "Keycloak realm's client settings and export it as an "
                "environment variable."
            )
        auth = KeycloakAuthClient(
            server_url=f"https://{HOST}/auth",
            client_id=CLIENT_ID,
            realm_name=KEYCLOAK_REALM,
            client_secret_key=CLIENT_SECRET,
            cert_path=CERT_PATH,
        )

    subscriber = Subscriber(auth)
    try:
        subscriber.run()
    except KeyboardInterrupt:
        log.info("Shutting down")
        subscriber.shutdown()


if __name__ == "__main__":
    main()
