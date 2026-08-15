# Release- und Upgrade-Richtlinie

## Definition von erledigt

Jede Änderung, die sich auf das Verhalten auswirkt, muss die Anforderungs-/Antwortmodelle aktualisieren.
Eingecheckter OpenAPI-Vertrag, Benutzer-/Betreiberdokumentation und Änderungsprotokoll im
gleiche Pull-Anfrage. `make check` ist das obligatorische lokale und CI-Gate. Es läuft
Backend-Suite, Frontend-Build/-Tests, PWA-Vertrag, OpenAPI-Drift-Check, geschützt
öffentlicher HTTPS-Vertrag und beide isolierten Akzeptanzwege:

```text
first Owner -> catalog/barcode -> synthetic receipt -> local stock
-> budget -> portable export -> operations overview

first login -> onboarding/update note -> invitation -> roles/account block
-> passkey -> TOTP -> recovery code -> password rotation
```

Die Reise nutzt eine temporäre Datenbank und synthetische Daten. Es wird nie eine Verbindung hergestellt
oder löscht einen bereitgestellten Haushalt.

Die vollständige Sequenz der ersten öffentlichen Veröffentlichung, einschließlich GitHub-Repository
Einstellungen und GHCR-Sichtbarkeit werden im beibehalten
[Checkliste für den öffentlichen Start](PUBLIC-LAUNCH-CHECKLIST.md).

## Containersicherung

– Laufzeit- und Build-Basis-Images werden durch Digest angeheftet.
- CI prüft vorher den kompletten Git-Verlauf mit der Digest-gepinnten Gitleaks-CLI
  Gebäude. Nur der exakte synthetische `YOUR_TOKEN`-Dokumentationsplatzhalter ist vorhanden
  auf die Zulassungsliste gesetzt; Die Ergebnisse bleiben in den Protokollen vollständig geschwärzt.
– CI erstellt die Produktions-Docker-Datei, schlägt bei behobenen „Hoch/Kritisch“-Ergebnissen fehl
  durch einen Digest-gepinnten offiziellen Grype-Container und erstellt einen CycloneDX JSON
  SBOM über einen offiziellen Syft-Container mit Digest-Pin. Dies vermeidet Laufzeit
  Installationsprogramm-Suchen, während der Scanner und die SBOM-Toolchain unveränderlich bleiben. Irgendein VEX
  Die Unterdrückung muss in `security/vex.openvex.json` erfolgen, einschließlich einer technischen
  Erreichbarkeitsbegründung und erneute Überprüfung auf Abhängigkeit oder Eingabe.
  Formatänderungen.
– GitHub-Aktionen von Drittanbietern sind an Full-Commit-SHAs angeheftet. Dependabot schlägt vor
  Wöchentlich gruppierte npm-, Python-, Docker- und Actions-Neben-/Patch-Updates zur Überprüfung;
  Größere Upgrades bleiben bewusste Arbeit des Betreuers, daher gilt dies auch für Kompatibilitätsänderungen
  den Freigabeprozess nicht überfluten oder umgehen.
- Ein `vMAJOR.MINOR.PATCH`-Tag muss genau mit `frontend/package.json` übereinstimmen.
- Ein Tag veröffentlicht `linux/amd64`- und `linux/arm64`-Bilder mit OCI in GHCR
  Etiketten, BuildKit-Herkunft und SBOM-Bescheinigung, dann signiert es schlüssellos
  unveränderlicher Digest mit Cosign. Derselbe Workflow erstellt die GitHub-Version
  und hängt die CycloneDX-SBOM sowie eine Textdatei an, die das Unveränderliche enthält
  Bildauszug.
– Der Tag-Workflow wiederholt `make check` und das feste Hoch/Kritisch-Bild-Gate
  vor dem Anmelden und Veröffentlichen, sodass sich ein Tag nicht nur auf einen vorherigen verlassen kann
  Zweiglauf.

Die private 0.8.23-Probe produzierte ein signiertes Multi-Architektur-Image, SBOM,
Release-Assets und ein unabhängiger Neuinstallationsnachweis. Keiner davon ist öffentlich
bis ein autorisierter Amturo-Betreuer die Repository- und Paketsichtbarkeit ändert
separat nach Passieren des Starttors. Version 0.8.26 ist der nächste Kandidat
und muss ein eigenes Tag, Bild, SBOM, Signatur und einen Neuinstallationsnachweis erhalten;
die unveränderlichen 0.8.23 Vermögenswerte werden nicht ersetzt.

## Private Veröffentlichungsprobe

Das erste Repository und das GHCR-Paket bleiben privat. CI läuft mit dem gleichen
Der für das öffentliche Projekt verwendete Workflow wird von einem authentifizierten Betreuer abgerufen
versioniertes Image auf einen zweiten Computer mit einem neuen Volume. Erst nach dem
Quellprüfung, Neuinstallation, Upgrade-/Wiederherstellungsprüfungen und signiertes Image
Bei der Überprüfung werden Repository- und Paketsichtbarkeit separat geändert
öffentlich. Private Haushaltsdaten und die bereitgestellte Haushaltsdatenbank sind niemals vorhanden
Teil dieser Probe.

## Überprüfen Sie ein zukünftiges öffentliches Bild

Ersetzen Sie den Beispielbesitzer/das Repository und die Version durch die veröffentlichten Werte:

```bash
docker pull ghcr.io/amturo-gbr/vorrio:0.8.26
cosign verify \
  --certificate-identity-regexp '^https://github.com/amturo-gbr/vorrio/.github/workflows/release.yml@refs/tags/v' \
  --certificate-oidc-issuer https://token.actions.githubusercontent.com \
  ghcr.io/amturo-gbr/vorrio:0.8.26
```

Heften Sie Produktionsbereitstellungen einer Version oder einem Digest zu. `latest` ist praktisch für
Evaluierung, keine Upgrade-Richtlinie.

## Kompatibilität und Upgrades

- Patch-Releases können Fehler und Sicherheitsprobleme beheben, ohne das zu ändern
  dokumentierter `/api/v1` Vertrag inkompatibel.
– Unterversionen können Felder und Endpunkte hinzufügen; Clients müssen unbekanntes JSON ignorieren
  Felder.
– Breaking API oder persistente Datenänderungen erfordern eine Hauptversion und sind explizit
  Migrationshinweise.
- Sichern Sie `/data` und `APP_SECRET_KEY`, lesen Sie `CHANGELOG.md` und aktualisieren Sie eine Version
  Zu einem Zeitpunkt, an dem es aufgrund von Notizen erforderlich ist, überprüfen Sie dann den Zustand, die Bereitschaft, die Anmeldung und die Anzahl
  und die PWA.
– Das Downgrade einer migrierten Datenbank wird nicht unterstützt. Stellen Sie das passende Backup wieder her.
