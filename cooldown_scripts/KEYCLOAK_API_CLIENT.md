# Keycloak client for the Python API scripts

Scripts such as `hello_world.py` authenticate to CS2 as a Keycloak client with a service account (client credentials flow). This page covers creating that client and getting its secret. Authentication is optional: if the CS2 instance runs without Keycloak, set `USE_AUTH = False` in the script and skip this page.

## Create the client

1. Log in to the Keycloak Admin console, realm `cs2`: `https://localhost/auth/admin/master/console/#/cs2/clients`. The default administrator login is documented in the CS2 manual.
2. Go to **Manage → Clients → Create client**.
3. **General settings:** set **Client ID** to `cs2_api_example`.
4. **Capability config:**
   - Turn **Client authentication** on.
   - Under authentication flow, enable only **Service accounts roles**.
5. **Login settings:** leave **Root URL** and **Home URL** empty, then save.

## Assign the roles (INTERNAL and SUPER)

1. Open the client's **Service account roles** tab.
2. Click **Assign role**.
3. Under **Filter by clients**, assign `INTERNAL` from `cs2-resource-server`.
4. Click **Assign role**. 
5. Change the filter from Filter by clients to Filter by realm roles. 
6. Tick `SUPER` and click Assign.

Without a CS2 role the token is valid but every API call fails with HTTP 500 (`Cannot invoke "java.util.Collection.size()" because "<parameter1>" is null`).

## Get the secret

1. Open the client's **Credentials** tab.
2. Copy the **Client secret**.
3. Export it in the terminal that runs the script:

PowerShell:

```powershell
$env:CS2_CLIENT_SECRET = "the-secret-from-keycloak"
```

bash / zsh:

```bash
export CS2_CLIENT_SECRET="the-secret-from-keycloak"
```

The variable lasts for that terminal session. Treat the secret like a password: don't commit it or paste it into a script.

## Script settings

The script's `KEYCLOAK_CLIENT_ID` and `KEYCLOAK_REALM` must match the client and realm above (`cs2_api_example`, `cs2`).
