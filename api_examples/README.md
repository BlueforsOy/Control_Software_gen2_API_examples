# API examples

This document walks through common interactions with Control Software 2 over
the HTTP API. Each block can be copied into your own code as a starting point.
Most error handling, retry logic etc. is omitted for clarity. See the top-level
README for notes on authentication and the API reference.

### Authentication

The `auth/` module provides a `KeycloakAuthClient` that handles fetching and
caching a bearer token. Construct it once and call `get_auth_token()` whenever
you need an `Authorization` header — it will reuse a cached token until it's
close to expiry, then refresh automatically.

By default the client verifies certificates against the OS trust store
(Windows cert store, macOS Keychain, system CAs on Linux), so CAs installed
through the usual corporate channels are picked up automatically. Otherwise you
can use `cert_path=` to trust an additional certificate on top of that.

```python
import os

from auth.keycloak import KeycloakAuthClient

CLIENT_SECRET = os.environ.get("CS2_CLIENT_SECRET")

auth = KeycloakAuthClient(
    server_url="https://localhost/auth",
    realm_name="cs2",
    client_id="cs2_api_example",
    client_secret_key=CLIENT_SECRET,
)

headers = {"Authorization": auth.get_auth_token()}
```

Full authentication flow is demonstrated in the next example. The following
ones omit it for clarity: the `headers` variable should contain a valid
authorization token, like shown.

## HTTP API

### Reading a value

```python
import json
import time
from urllib import request, parse

from auth.keycloak import KeycloakAuthClient

CLIENT_SECRET = os.environ.get("CS2_CLIENT_SECRET")

auth = KeycloakAuthClient(
    server_url="https://localhost/auth",
    realm_name="cs2",
    client_id="cs2_api_example",
    client_secret_key=CLIENT_SECRET,
)

url = "https://localhost/api/v1"
device_id = "V104"

headers = {"Authorization": auth.get_auth_token()}
req = request.Request(f"{url}/state/devices/{device_id}", headers=headers)

with request.urlopen(req) as response:
    print(json.load(response))
```

### Monitoring a value by polling

```python
import json
import time
from urllib import request

url = "https://localhost/api/v1"
device_id = "V104"

# Press Ctrl+C to stop the loop.
while True:
    req = request.Request(f"{url}/state/devices/{device_id}", headers=headers)
    with request.urlopen(req) as response:
        print(json.load(response))
        time.sleep(1)
```

### Opening and closing a valve

```python
import json
import uuid
from urllib import request

url = "https://localhost/api/v1"

device_id = "V104"  # or "plc.ValveGroup.Valve104"

# Opening the valve
command = {
    "commandId": "command",
    "correlationId": str(uuid.uuid4()),
    "payload": {"valveOnOff": True},
}

post_headers = {**headers, "Content-Type": "application/json"}
req = request.Request(
    f"{url}/devices/{device_id}/command",
    data=json.dumps(command).encode("utf-8"),
    headers=post_headers,
    method="POST",
)
with request.urlopen(req) as response:
    print(json.load(response))

# Closing the valve
command["correlationId"] = str(uuid.uuid4())
command["payload"]["valveOnOff"] = False

req = request.Request(
    f"{url}/devices/{device_id}/command",
    data=json.dumps(command).encode("utf-8"),
    headers=post_headers,
    method="POST",
)
with request.urlopen(req) as response:
    print(json.load(response))
```

### Setting power to a still heater

Still heater has two separate mappings: one for the on/off state
(`STILL_HEATER`) and one for the power setpoint (`STILL_HEATING_POWER`).
Turning the heater on and setting a power are separate commands.

Turning the heater on:

```python
import json
import uuid
from urllib import request

url = "https://localhost/api/v1"

device_id = "STILL_HEATER"
command = {
    "commandId": "command",
    "correlationId": str(uuid.uuid4()),
    "payload": {"heaterOnOff": True},
}
post_headers = {**headers, "Content-Type": "application/json"}
req = request.Request(
    f"{url}/devices/{device_id}/command",
    data=json.dumps(command).encode("utf-8"),
    headers=post_headers,
    method="POST",
)
with request.urlopen(req) as response:
    print(json.load(response))
```

Setting power:

```python
import json
import uuid
from urllib import request

url = "https://localhost/api/v1"

device_id = "STILL_HEATING_POWER"
heater_channel = "3"
command = {
    "commandId": "write",
    "correlationId": str(uuid.uuid4()),
    "payload": {"heaters": {heater_channel: {"params": {"power": 0.010}}}},
}
post_headers = {**headers, "Content-Type": "application/json"}
req = request.Request(
    f"{url}/devices/{device_id}/command",
    data=json.dumps(command).encode("utf-8"),
    headers=post_headers,
    method="POST",
)
with request.urlopen(req) as response:
    print(json.load(response))
```

Turning the heater off:

```python
import json
import uuid
from urllib import request

url = "https://localhost/api/v1"

device_id = "STILL_HEATER"
command = {
    "commandId": "command",
    "correlationId": str(uuid.uuid4()),
    "payload": {"heaterOnOff": False},
}
post_headers = {**headers, "Content-Type": "application/json"}
req = request.Request(
    f"{url}/devices/{device_id}/command",
    data=json.dumps(command).encode("utf-8"),
    headers=post_headers,
    method="POST",
)
with request.urlopen(req) as response:
    print(json.load(response))
```

### Interacting with the Operations API

```python
import json
import uuid
from urllib import request, parse

url = "https://localhost/api/v1"

# Getting available operations
req = request.Request(f"{url}/operations?includeInvalid=true", headers=headers)
with request.urlopen(req) as response:
    print(json.load(response))
```

```python
import json
import uuid
from urllib import request, parse

# Starting an operation
operation_name = "Manual"
parameters = {}

post_headers = {**headers, "Content-Type": "application/json"}
req = request.Request(
    f"{url}/operations/{parse.quote(operation_name)}/start",
    data=json.dumps(parameters).encode("utf-8"),
    headers=post_headers,
    method="POST",
)
with request.urlopen(req) as response:
    print(json.load(response))
```

### Fetching and plotting values
Requires `matplotlib`.

```python
import datetime
import json
import time
from urllib import request, parse

import matplotlib.pyplot as plt

#### Specify which device is searched for what time period
device_id = "P3_PRESSURE"

#### Use time format like "%Y-%m-%dT%H:%M:%S.%fZ"
end_time = datetime.datetime.now()
start_time = end_time - datetime.timedelta(days=7)
time_format = "%Y-%m-%dT%H:%M:%S.%fZ"

#### Use the variables to form the API call
query = parse.urlencode({
    "from": start_time.strftime(time_format),
    "to": end_time.strftime(time_format),
    "format": "array",
})
req = request.Request(
    f"{url}/events/values/{parse.quote(device_id)}?{query}",
    headers=headers,
    method="GET",
)
with request.urlopen(req) as r:
    response = json.load(r)

#### Fetch the correct values from the JSON-object
temperatures = response["value"]
datetime_strings = response["datetime"]

#### Format the datetime objects correctly
timestamps = []
for dt in datetime_strings:
    timestamps.append(datetime.datetime.strptime(dt, time_format))

#### Plot the data
fig, ax = plt.subplots()
ax.plot(timestamps, temperatures)

ax.set(
    xlabel="datetime (s)",
    ylabel="temperature (mK)",
    title=f"Temperature of {device_id}",
)
plt.show()
```
