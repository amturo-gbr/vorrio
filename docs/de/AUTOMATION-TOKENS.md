# Automatisierungs-API-Tokens

Vorrio 0.8.14 bietet eingeschränkte Anmeldeinformationen für Home Assistant, Keyboard-Wedge
Scannerstationen und andere lokale Dienste. Sie ersetzen kopierte Browser-Cookies
oder gemeinsame Haushaltspasswörter.

## Erstellen Sie ein Token

1. Melden Sie sich als Besitzer oder Administrator an.
2. Öffnen Sie **Einstellungen → Konto & Sicherheit → API-Tokens**.
3. Bestätigen Sie die aktuelle Identität, wenn das zehnminütige Sicherheitsfenster abgelaufen ist.
4. Wählen Sie **Home Assistant · nur lesen**, **Handscanner · Scanaktionen** oder a
   Benutzerdefinierter Bereichssatz.
5. Wählen Sie einen Namen und eine Lebensdauer, erstellen Sie den Token und kopieren Sie den Rohwert
   sofort. Vorrio kann es nicht erneut anzeigen.

Der Wert beginnt mit `vor_pat_`. Speichern Sie es im Geheimnis des Zieldienstes
Speichern und senden Sie es nur über eine vertrauenswürdige HTTPS/VPN-Verbindung:

```http
Authorization: Bearer vor_pat_example_secret
```

Platzieren Sie es nicht in einem URL-, Repository- oder Dashboard-Textfeld, das für andere sichtbar ist
Benutzer- oder Anwendungsprotokoll.

## Bereiche

| Geltungsbereich | API-Oberfläche |
|---|---|
| `status:read` | `GET /api/v1/status` |
| `catalog:read` | Schreibgeschützte `/api/v1/catalog/*`-Vorgänge |
| `stock:read` | Schreibgeschützte `/api/v1/stock/*`-Vorgänge |
| `shopping:read` | Einkaufsliste und Vorschau auf geringe Lagerbestände |
| `shopping:write` | Überprüfte Generations- und Listenelementmutationen |
| `scans:read` | Entwürfe und ungelöste Posteingänge scannen |
| `scans:write` | Scan-Entwürfe auflösen, bearbeiten, bestätigen und verwerfen |

OpenAPI fügt `x-vorrio-required-scope` zu jeder Bearer-aktivierten Operation hinzu.
Identität, Einstellungen, Konnektoren, Hochladen/Analyse von Belegen, direkte Katalogschreibvorgänge
und Schreibvorgänge zur Bestandszählung bleiben nur in der Browsersitzung bestehen.

## Testen Sie ein schreibgeschütztes Token

```bash
curl --fail --silent --show-error \
  -H 'Authorization: Bearer YOUR_TOKEN' \
  https://vorrio.example.test/api/v1/status
```

Behalten Sie für Home Assistant den Wert in `secrets.yaml` bei und verweisen Sie darauf
REST-Integration statt direkt in der Konfiguration zu platzieren:

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

Speichern Sie den vollständigen Wert `Bearer vor_pat_…` als
`vorrio_authorization_header` in `secrets.yaml`. Home Assistant YAML-Geheimnis
Substitutionsregeln können je nach Integration und Release variieren; Verwenden Sie ein unterstütztes REST
Paketmuster und übergeben Sie niemals das resultierende Token.

## Scanner-Anfrage

Ein Scanner-Client erstellt zunächst einen reinen Überprüfungsentwurf. Es muss noch angezeigt werden
Ergebnis und holen Sie eine explizite Bestätigung ein, bevor Sie den Bestätigungsendpunkt aufrufen:

```bash
curl --fail --silent --show-error \
  -H 'Authorization: Bearer YOUR_TOKEN' \
  -H 'Content-Type: application/json' \
  --data '{"barcode":"4000000000016","mode":"identify","client_mutation_id":"device-unique-id"}' \
  https://vorrio.example.test/api/v1/scans/resolve
```

Verwenden Sie für Wiederholungsversuche ein eindeutiges, stabiles `client_mutation_id`. Die vollständige Bestätigung
Anfrage- und Antwortmodelle werden in der Swagger-Benutzeroberfläche dokumentiert und eingecheckt
OpenAPI-Vertrag.

## Rotation und Reaktion auf Vorfälle

- Verwenden Sie den kleinsten Zielfernrohrsatz und die kürzeste praktische Lebensdauer.
- Erstellen Sie einen Ersatz, aktualisieren Sie den Zieldienst, überprüfen Sie ihn und widerrufen Sie ihn dann
  vorheriges Token.
- Widerrufen Sie Anmeldeinformationen sofort, wenn ein Gerät verloren geht oder ausgemustert wird.
- Durch das Sperren des Erstellerkontos oder der Haushaltsmitgliedschaft wird auch dieses deaktiviert
  Token.
– Ein ungültiger Bearer-Header greift niemals auf einen ansonsten gültigen Browser zurück
  Keks.
- Datenbanksicherungen enthalten Token-Hashes und Metadaten, niemals den Rohträger
  Wert.
