This module contains an example authentication client for Keycloak, that
handles the initial authentication, access token fetching and refresh.

Note that the authentication tokens have a limited lifespan: When the token is
fetched, it comes with an `expires_in` field. The authentication tokens should
be refreshed before this time. Your HTTP requests should make sure to use a
fresh token, by calling `KeycloakAuthClient.get_auth_token()` and adding it to
the request headers when sending the request. You can't just fetch the token
once and use it indefinitely.

The access token lifespan can be configured under **Realm settings** in the
Keycloak Admin if necessary.

# Obtaining the client secret key

Access the Keycloak Admin console at <https://localhost/auth/admin/master/console/#/cs2>.

Create a new client under **Manage → Clients → Create client**.

**Step 1 — General Settings**

- Client ID: e.g. `cs2_api_example`

**Step 2 — Capability Config**

- Client authentication: **On**
- Authentication flow: enable **Service accounts roles** only

**Step 3 — Login Settings**

- Root URL and Home URL can be left empty

After saving, go to the **Service account roles** tab, click **Assign role**, and assign the `INTERNAL` role from `cs2-resource-server`. Then add the `READ_ONLY` role by selecting **Filter by Realm roles**.

Then go to the **Credentials** tab to copy the generated client secret.

Set `CLIENT_ID` in the example script to match what you created above, and export the secret as an environment variable before running.

PowerShell:

```powershell
$env:CS2_CLIENT_SECRET = "the-secret-from-keycloak"
```

bash / zsh:

```bash
export CS2_CLIENT_SECRET="the-secret-from-keycloak"
```
