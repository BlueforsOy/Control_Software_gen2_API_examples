# Bluefors Control Software 2 — Python examples

This repository contains Python scripts for monitoring values over HTTP API or
websocket, and sending commands to devices over the HTTP API, for Bluefors
Control Software 2. They are meant as examples, or a starting point for users
to start implementing their own scripts. Most error handling, retry logic etc.
is omitted for clarity.

**Note: Some examples use https://localhost as the CS2 base URL. On Windows, we
have noticed that resolving localhost can sometimes be slow. In that case, you
can try using https://127.0.0.1 instead.**

## Authentication

Control Software 2 uses [Keycloak](https://www.keycloak.org/) for
authentication. The examples show how to obtain and refresh a token, and how
to pass it on subsequent HTTP and websocket calls.

### SSL/TLS

The API is served over HTTPS, so the machine running the scripts needs to
recognize CS2's certificate as valid. Depending on the install method, this
may already be set up:

- **Debian (IPC):** the installer generates a self-signed certificate and
  registers it with the system trust store, so scripts running on the IPC
  can verify the connection against the OS trust store with no extra
  configuration.
- **Windows:** the installer does not currently register the certificate
  with the Windows trust store. Either install the certificate, or point
  the examples at the certificate file directly with `cert_path=` (see the
  configuration in each example).
- **Managed environments:** in a corporate or institutional setting, your
  IT department may have already deployed the CS2 certificate (or a CA that
  signed it) to client machines through group policy or a similar mechanism.
  If so, no extra configuration is needed on your end.

The same applies if you're connecting to a CS2 instance from a different
machine than the one it's installed on: the certificate needs to be in that
machine's trust store, or passed via `cert_path=`.

On Linux and Windows, the Python Standard Library's `urllib` uses the system
trust store by default; no explicit SSL context needs to be passed in if you
are using the system trust store.

Note that Python's HTTP libraries (at least `requests`) don't always use the
system trust store by default — behaviour varies by platform and library. For a
consistent cross-platform solution, you can use the
[`truststore`](https://pypi.org/project/truststore/) package, which reads from
the OS trust store on Debian, Windows, and macOS.


## API reference

The full API reference is hosted by Control Software 2 itself and available
at:

    https://<CS2_HOST>/api/v1/swagger-ui/index.html

Replace `<CS2_HOST>` with the hostname or IP address of your CS2 instance.

## Requirements

Python 3.10+. See `requirements.txt` for the tested package versions.
