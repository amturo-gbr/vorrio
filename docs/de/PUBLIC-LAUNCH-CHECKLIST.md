# Checkliste für den öffentlichen Start

Dieses Tor ist für die erste öffentliche Amturo-Veröffentlichung vorgesehen. Ein erfolgreicher lokaler Build ist
erforderlich, veröffentlicht jedoch selbst kein Repository oder Container.

## 1. Quelle und Identität

- [ ] Das Repository wird als `amturo-gbr/vorrio` ohne generierte README-Datei oder erstellt
  Lizenz, die mit diesem Quellbaum in Konflikt geraten könnte.
- [ ] Der Standardzweig ist `main` und die Repository-Beschreibung, Themen und
  Die Lizenz AGPL-3.0 oder höher ist sichtbar.
- [ ] `README.md`, `LICENSE`, `NOTICE`, `AUTHORS.md`, `CONTRIBUTING.md`,
  `SECURITY.md`, Supportmaterial und das Änderungsprotokoll werden korrekt dargestellt.
- [ ] Keine Quittung, Datenbank, `.env`, API-Schlüssel, Cookie, privater Hostname, LAN
  Adresse, persönlicher Pfad oder generiertes lokales Artefakt wird inszeniert.
- [ ] Amturo hat die absichtlich öffentliche Unternehmensidentität erneut überprüft und verwaltet
  Direktoren, eingetragener Sitz, Registerdetails, Telefonnummer und Sicherheit
  E-Mail in beiden Impressum-/Datenschutzvarianten.
- [ ] Der vollständige Verlauf des geheimen Scans und der Release-Package-Identitätsvertragsdurchlauf
  ohne unerklärlichen Zulassungslisteneintrag.
- [ ] Unmittelbar nach der Aktivierung der öffentlichen Sichtbarkeit und vor der Ankündigung,
  Aktivieren Sie die private Schwachstellenberichterstattung von GitHub und überprüfen Sie den Empfehlungslink
  über einen abgemeldeten Browser.

## 2. Release-Kandidat

- [ ] `make check` geht von einem sauberen Checkout aus.
- [ ] Die automatisierten Dokumentations-Link- und Release-Paket-Hygieneprüfungen bestehen.
  Letzterer sieht genau die verfolgten und nicht ignorierten Dateien, die für GitHub bestimmt sind.
- [ ] Das Release-Tag stimmt genau mit `frontend/package.json` überein.
- [ ] Desktop- und 390-Pixel-Mobil-UAT-Cover-Einrichtung/Anmeldung, alle fünf Navigationsmöglichkeiten
  Bereiche, Scanneraktionen, Quittungsprüfung, Katalog-/Zählungsprüfung, Einkaufsregisterkarten,
  Feedback zu Einstellungen und Abmeldung ohne Konsolenfehler.
- [ ] Zerstörerische Datenschutzmaßnahmen wirken sich nur gegen den synthetischen Launch-Smoke aus
  Datenbank.
- [ ] Das Produktionsimage weist keine feste Schwachstellenfeststellung „Hoch“ oder „Kritisch“ auf;
  Jede VEX-Anweisung verfügt weiterhin über eine aktuelle Erreichbarkeitsbegründung.
- [ ] Ein CycloneDX SBOM wird generiert und das Image wird als nicht privilegiertes ausgeführt
  Anwendungsbenutzer mit einem persistenten `/data`-Volume.

## 3. GitHub-Steuerelemente

- [ ] CI ist für Pull-Anfragen an `main` erforderlich.
- [ ] Direktes Force-Push und Zweiglöschung sind blockiert.
- [ ] Dependabot-Sicherheits- und Versionsaktualisierungen sind aktiviert.
- [ ] Geheimes Scannen und Push-Schutz sind im GitHub-Plan aktiviert
  unterstützt sie.
- [ ] Wenn Einschränkungen des privaten Repository-Plans Regelsätze verhinderten, erstellen Sie und
  Überprüfen Sie den Zweigregelsatz `main` sofort nach dem Ändern der Sichtbarkeit und
  bevor Sie Beiträge annehmen oder das Projekt ankündigen.
- [ ] Vorschläge zur Abhängigkeitsaktualisierung nutzen die siebentägige Abklingzeit und bleiben gruppiert
  nach Ökosystem; Größere Upgrades erfordern eine bewusste Überprüfung durch den Betreuer.
- [ ] Diskussionen, Problemvorlagen und die Support-/Sicherheitsrouten weisen auf Benutzer hin
  zum richtigen Kanal.
- [ ] `CODEOWNERS` wird zu einem aktiven Betreuer aufgelöst; Sprachanfrage und
  Pull-Request-Vorlagen für Sprachpakete werden von einem abgemeldeten Benutzer korrekt dargestellt
  Mitwirkenderfluss.
- [ ] Übersetzungs-Workflow-Labels (`language:requested`, `language:in-progress`,
  `language:needs-review`, `language:verified`, `language:official`) existieren und
  Der Community-Leitfaden ist über die README-Datei und die Beitragsdokumentation verlinkt.
- [ ] Die statische Projektwebsite wird auf dem Desktop mit 1440 Pixeln und auf Mobilgeräten mit 390 Pixeln gerendert.
  Alle veröffentlichten Links funktionieren anonym und jeder Screenshot verwendet synthetische Daten.
- [ ] Deutsch und Englisch vervollständigen das gleiche Abmelden, Onboarding, Empfang,
  Scanner, Katalog, Einkaufen, Einstellungen, Fehler und mobile Layout-Reise; die
  Der automatisierte i18n-Vertrag meldet keine fehlende oder umgangene Kopie.
- [ ] Offizielle Sprachmanifeste und der Nur-Daten-Paketvalidierungspass; NEIN
  Die Laufzeit-Community-Paketquelle wird vor der Signaturüberprüfung aktiviert.
- [ ] Das gesetzlich genehmigte Impressum und die Datenschutzerklärung von Amturo sind vorhanden
  über den eingesetzten Ursprung vor der öffentlichen Ankündigung.
- [ ] `vorrio.app` wird als kanonische Vercel-Domäne verifiziert, `vorrio.de`
  gibt eine permanente Umleitung mit demselben Pfad zu `.app` und beiden HTTPS-Zertifikaten zurück
  gelten auch nach der IONOS DNS-Änderung.

## 4. Erste GHCR-Veröffentlichung

- [ ] Drücken Sie `main` und warten Sie, bis der CI-Workflow abgeschlossen ist.
- [ ] Erstellen und pushen Sie das versionierte Release-Tag `v0.8.27` erst, nachdem CI bestanden hat und
  Die private Veröffentlichungsprobe ist bereit für ihren unveränderlichen Kandidaten.
- [ ] Bestätigen Sie, dass der Release-Workflow `linux/amd64` und `linux/arm64` erstellt.
  veröffentlicht Provenienz-/SBOM-Bescheinigungen und unterzeichnet den unveränderlichen Digest.
- [ ] Bestätige nach bestandener isolierter Probe, dass das GHCR-Paket
  öffentlich, mit dem Repository verknüpft und anonym abrufbar ist.
- [ ] Ziehen Sie das versionierte Image auf einen zweiten Computer und schließen Sie die erste Einrichtung mit ab
  ein frisches Volumen.
- [ ] Überprüfen Sie die Signatur und die Integritäts-/Bereitschaftsendpunkte mit den Befehlen in
  [Veröffentlichungs- und Upgrade-Richtlinie](RELEASES.md).

## 5. Installations- und Wiederherstellungsnachweis

- [ ] Testen Sie sowohl Source-Build Compose als auch das veröffentlichte GHCR Compose-Beispiel.
- [ ] Überprüfen Sie die Nur-LAN-Standardeinstellungen, die private HTTPS/PWA-Installation und die geschützte Installation
  public-HTTPS-Profil separat.
- [ ] Sichern Sie `/data` und `APP_SECRET_KEY` und stellen Sie sie in einem neuen Container wieder her.
  und vergleichen Sie Login-, Produkt-, Empfangs- und Lagerbestände.
- [ ] Bestätigen Sie die Upgrade-Hinweise, die Downgrade-Warnung und die Supportgrenzen im
  öffentliche Versionshinweise.

## 6. Nach der Veröffentlichung

- [] Öffnen Sie die öffentliche README-Datei, die API-Dokumentation und die Containerseite und generieren Sie sie
  Freigabe über einen abgemeldeten Browser.
- [ ] Installieren Sie den genauen veröffentlichten Digest einmal und wiederholen Sie den Startrauch.
- [ ] Erfassen Sie den freigegebenen Digest, den CI-Lauf und das SBOM-Artefakt in den Versionshinweisen.
- [ ] Ankündigung erst nach der Installation, Signaturprüfung und Erstanmeldung
  Die Genesung ist alle vorbei.
- [ ] Aktivieren Sie die Stripe-Zahlungslinks der Website erst nach dem Amturo-Geschäft
  Konto, Live-Links, Datenschutzbestimmungen, Mehrwertsteuerbehandlung und Buchhaltungsprozess
  sind genehmigt; Halten Sie GitHub-Sponsoren verborgen.

Der Betreuer überprüft jedes Kästchen anhand öffentlicher oder synthetischer Daten. Ein Privatmann
Die Haushaltsinstallation dient niemals als Freigabebeweis und bedarf keiner solchen
öffentliche Cloudflare-Route.
