"""All functions that communicate with the CS2 API and classes used in the cooldown_scripts scripts."""

import os
import json
import time
import logging
import uuid
from urllib import request, parse, error

from configuration import (
    CERT_PATH,
    CS2_API_URL,
    KEYCLOAK_CLIENT_ID,
    KEYCLOAK_CLIENT_SECRET,
    KEYCLOAK_REALM,
    KEYCLOAK_URL,
    USE_AUTH,
)
from keycloak_auth import KeycloakAuthClient, NoAuthClient

log = logging.getLogger(__name__)


# Configure once at startup.
if USE_AUTH:
    _auth = KeycloakAuthClient(
        server_url=KEYCLOAK_URL,
        client_id=KEYCLOAK_CLIENT_ID,
        realm_name=KEYCLOAK_REALM,
        client_secret_key=KEYCLOAK_CLIENT_SECRET,
        cert_path=CERT_PATH,
    )
else:
    _auth = NoAuthClient(cert_path=CERT_PATH)


def _do_request(url, method, body=None):
    """Single attempt. Returns parsed JSON. Raises HTTPError on failure."""
    headers = _auth.get_auth_headers()
    data = None
    if body is not None:
        data = json.dumps(body).encode("utf-8")
        headers["Content-Type"] = "application/json"

    req = request.Request(url, method=method, data=data, headers=headers)
    # Reuse the auth client's SSL context so cert config lives in one place.
    with request.urlopen(req, context=_auth.ssl_context) as res:
        return json.load(res)


def _request(url, method="GET", body=None):
    """Request with auth, retrying once on 401 in case the token was revoked early."""
    try:
        return _do_request(url, method, body)
    except error.HTTPError as e:
        if e.code != 401:
            raise
        _auth.token = None  # force re-fetch on next get_auth_token() call
        return _do_request(url, method, body)


def _command(device_id, payload, command_id="command"):
    try:
        result = _request(
            f"{CS2_API_URL}/devices/{device_id}/command",
            method="POST",
            body={
                "commandId": command_id,
                "correlationId": str(uuid.uuid4()),
                "payload": payload,
            },
        )
    except error.HTTPError as e:
        if e.code == 404:  # handle calls to missing devices
            log.warning("Skipping %s: device not present", device_id)
            return None
        raise
    log.info(result)
    return result


def value(mapping):
    data = _request(f"{CS2_API_URL}/state/devices?keys={parse.quote(mapping)}")
    return data[mapping]


def valves_on(valves: list):
    for valve in valves:
        _command(valve, {"valveOnOff": True})


def valves_off(valves: list):
    for valve in valves:
        _command(valve, {"valveOnOff": False})


def pump_on(pump):
    _command(pump, {"pumpStartStop": True})


def pump_off(pump):
    _command(pump, {"pumpStartStop": False})


def heater_on(heaters: list):
    for heater in heaters:
        _command(heater, {"heaterOnOff": True})


def heater_off(heaters: list):
    for heater in heaters:
        _command(heater, {"heaterOnOff": False})


def set_heater_power(heater, power: float):
    _command(
        heater[0],
        {"heaters": {heater[1]: {"params": {"power": power}}}},
        command_id="write",
    )


def pulse_tube_on(pulse_tube):
    _command(pulse_tube, {"pulseTubeStartStop": True})


def pulse_tube_off(pulse_tube):
    _command(pulse_tube, {"pulseTubeStartStop": False})


def set_cold_cathode(device_id):
    _command(device_id, {"activateColdCathode": True})


def warmup_heater_1_on(device_id):
    _command(device_id, {"params": {"b4KHeater1RelayOnOff": True}}, command_id="write")


def warmup_heater_1_off(device_id):
    _command(device_id, {"params": {"b4KHeater1RelayOnOff": False}}, command_id="write")


def warmup_heater_2_on(device_id):
    _command(device_id, {"params": {"b4KHeater2RelayOnOff": True}}, command_id="write")


def warmup_heater_2_off(device_id):
    _command(device_id, {"params": {"b4KHeater2RelayOnOff": False}}, command_id="write")


def circulation_turbo_pumps_on(device_id):
    _command(device_id, {"turboPumpsStartStop": True})


def circulation_turbo_pumps_off(device_id):
    _command(device_id, {"turboPumpsStartStop": False})


def enable_fse():
    _command("FSE", {"params": {"bFSE_Enable": True}}, command_id="write")


def disable_fse():
    _command("FSE", {"params": {"bFSE_Enable": False}}, command_id="write")


def fse_target(target_position):
    _command(
        "FSE", {"params": {"fTargetPosition": target_position}}, command_id="write"
    )


def fse_motor_start():
    _command("FSE", {"params": {"bMotorStartSW": True}}, command_id="write")


def fse_motor_stop():
    _command("FSE", {"params": {"bMotorStopSW": True}}, command_id="write")


def enable_fse_fan():
    _command("FSE", {"params": {"bFanCMD": True}}, command_id="write")


def disable_fse_fan():
    _command("FSE", {"params": {"bFanCMD": False}}, command_id="write")


def enable_fse_heater():
    _command("FSE", {"params": {"bHeaterCMD": True}}, command_id="write")


def disable_fse_heater():
    _command("FSE", {"params": {"bHeaterCMD": False}}, command_id="write")


# Timer class to enable time-based loops
class Timer:
    def __init__(self):
        self.start = time.time()

    def reset(self):
        self.start = time.time()

    def elapsed(self):
        return time.time() - self.start

    def __str__(self):
        return f"Time elapsed: {time.time() - self.start} seconds"

    def __gt__(self, other):
        return (time.time() - self.start) > other

    def __lt__(self, other):
        return (time.time() - self.start) < other

    def __eq__(self, other):
        return (time.time() - self.start) == other


class ErrorState(Exception):
    pass
