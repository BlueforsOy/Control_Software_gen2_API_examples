# Websocket

Communication uses the [STOMP protocol](https://stomp.github.io/) over
websocket.

## Prerequisites

- Python 3.10+
- `stomp.py` installed (`pip install "stomp.py[websocket]"`)
- A running CS2 instance
- A Keycloak client set up for the `cs2` realm — see `auth/README.md` for
instructions


### Monitoring values

```python
import stomp  # https://github.com/jasonrbriggs/stomp.py

url = "localhost"
port = 443
websocket_path = "/socket"

conn = stomp.WSConnection([(url, port)], ws_path=websocket_path)

conn.set_listener("", stomp.listener.PrintingListener())
conn.connect(wait=True)
conn.subscribe(destination="/topic/events/devices", id=1, ack="auto")
conn.subscribe(destination="/topic/events/values", id=2, ack="auto")
conn.subscribe(destination="/topic/state/statemachine", id=3, ack="auto")

conn.disconnect()
```

### Custom listener: monitor a single value

```python
import json
import stomp

url = "127.0.0.1"
port = 443
websocket_path = "/socket"


class StillTemperatureListener(stomp.ConnectionListener):
    def on_error(self, frame):
        print('received an error "%s"' % frame.body)

    def on_message(self, frame):
        msg = json.loads(frame.body)
        if msg["valueId"] == "value4bool.bValue1":
            print(f"{msg['datetime']}: {msg['value']}")


conn = stomp.WSConnection([(url, port)], ws_path=websocket_path)
conn.set_listener("", StillTemperatureListener())
conn.connect(wait=True)
conn.subscribe(destination="/topic/events/values", id=1, ack="auto")

conn.disconnect()
```

## Example with authentication
### Configure

Open `monitoring.py` and adjust the values at the top if needed:

- `HOST`, `PORT`, `VHOST` — the CS2 server
- `CERT_PATH` — path to the server's certificate (used for both the WebSocket
connection and the Keycloak token request)
- `CLIENT_ID` — must match the client you created in Keycloak
- `SUBSCRIPTIONS` — list of `(subscription_id, topic)` pairs to subscribe to
- `USE_AUTH` — set to `False` if your CS2 instance runs without Keycloak

Export the client secret you copied from Keycloak.

PowerShell:

```powershell $env:CS2_CLIENT_SECRET = "the-secret-from-keycloak" ```

bash / zsh:

```bash export CS2_CLIENT_SECRET="the-secret-from-keycloak" ```

### Run

From the repo root:

``` python -m websocket_example.monitoring ```

You should see `CONNECTED`, then a `Subscribed to ...` line for each topic,
then `MESSAGE: ...` entries as events arrive. Stop with Ctrl+C.
