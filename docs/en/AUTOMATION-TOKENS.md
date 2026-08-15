# Automation API tokens

Vorrio 0.8.14 provides scoped credentials for Home Assistant, keyboard-wedge
scanner stations and other local services. They replace copied browser cookies
or shared household passwords.

## Create a token

1. Sign in as Owner or Admin.
2. Open **Einstellungen → Konto & Sicherheit → API-Tokens**.
3. Confirm the current identity if the ten-minute security window has expired.
4. Choose **Home Assistant · nur lesen**, **Handscanner · Scanaktionen** or a
   custom scope set.
5. Choose a name and lifetime, create the token and copy the raw value
   immediately. Vorrio cannot display it again.

The value starts with `vor_pat_`. Store it in the target service's secret
store and send it only over a trusted HTTPS/VPN connection:

```http
Authorization: Bearer vor_pat_example_secret
```

Do not put it in a URL, repository, dashboard text field visible to other
users or application log.

## Scopes

| Scope | API surface |
|---|---|
| `status:read` | `GET /api/v1/status` |
| `catalog:read` | Read-only `/api/v1/catalog/*` operations |
| `stock:read` | Read-only `/api/v1/stock/*` operations |
| `shopping:read` | Shopping list and low-stock preview |
| `shopping:write` | Reviewed generation and list-item mutations |
| `scans:read` | Scan drafts and unresolved inbox |
| `scans:write` | Resolve, edit, confirm and discard scan drafts |

OpenAPI adds `x-vorrio-required-scope` to every bearer-enabled operation.
Identity, settings, connectors, receipt upload/analysis, direct catalog writes
and stock-count writes remain browser-session only.

## Test a read-only token

```bash
curl --fail --silent --show-error \
  -H 'Authorization: Bearer YOUR_TOKEN' \
  https://vorrio.example.test/api/v1/status
```

For Home Assistant, keep the value in `secrets.yaml` and reference it from the
REST integration instead of placing it directly in configuration:

```yaml
rest:
  - resource: https://vorrio.example.test/api/v1/status
    headers:
      Authorization: !secret vorrio_authorization_header
    verify_ssl: true
    scan_interval: 300
    sensor:
      - name: Vorrio Produkte
        value_template: "{{ value_json.catalog.products }}"
```

Store the complete value `Bearer vor_pat_…` as
`vorrio_authorization_header` in `secrets.yaml`. Home Assistant YAML secret
substitution rules can vary by integration and release; use a supported REST
package pattern and never commit the resulting token.

## Scanner request

A scanner client first creates a review-only draft. It must still show the
result and obtain explicit confirmation before calling the confirm endpoint:

```bash
curl --fail --silent --show-error \
  -H 'Authorization: Bearer YOUR_TOKEN' \
  -H 'Content-Type: application/json' \
  --data '{"barcode":"4000000000016","mode":"identify","client_mutation_id":"device-unique-id"}' \
  https://vorrio.example.test/api/v1/scans/resolve
```

Use a unique, stable `client_mutation_id` for retries. The full confirmation
request and response models are documented in Swagger UI and the checked-in
OpenAPI contract.

## Rotation and incident response

- Use the smallest scope set and shortest practical lifetime.
- Create a replacement, update the target service, verify it, then revoke the
  previous token.
- Revoke a credential immediately when a device is lost or retired.
- Blocking the creator account or household membership also disables its
  tokens.
- An invalid bearer header never falls back to an otherwise valid browser
  cookie.
- Database backups contain token hashes and metadata, never the raw bearer
  value.
