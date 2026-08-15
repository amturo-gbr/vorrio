# Installation

## Anforderungen

- Docker Engine 24 oder neuer;
- Docker Compose v2;
- 1 CPU-Kern und 512 MB RAM für die Anwendung;
- persistenter lokaler Speicher für `/data`;
- ein Analyseanbieter, es sei denn, es wird ein lokales Ollama-kompatibles Modell verwendet.

SQLite sollte auf einem lokalen Docker-Volume bleiben. Vermeiden Sie Netzwerkdateisysteme, die dies tun
bietet keine zuverlässige Dateisperre.

## Docker Compose

```bash
git clone https://github.com/amturo-gbr/vorrio.git
cd vorrio
cp .env.example .env
openssl rand -hex 32
```

Platzieren Sie den generierten Wert in `.env` als `APP_SECRET_KEY` und starten Sie dann:

```bash
docker compose up -d --build
docker compose ps
```

Öffnen Sie `http://SERVER:9380`, benennen Sie den ersten Besitzer und schließen Sie die Passworteinrichtung ab.
Der Setup-Bildschirm folgt den deutschen oder englischen Browsereinstellungen und speichert die
ausgewählte Schnittstellensprache für diesen Besitzer. Es kann später pro Benutzer geändert werden
ohne den Container umzubauen.

Ersetzen Sie bei einer LAN-Installation den Platzhalter durch die genauen verwendeten Namen oder IPs
von Browsern, wann immer möglich:

```env
DEPLOYMENT_PROFILE=lan
TRUSTED_HOSTS=localhost,vorrio.lan,192.0.2.10
FORWARDED_ALLOW_IPS=127.0.0.1
SESSION_HTTPS_ONLY=false
```

Die Dokumentationsadresse ist reserviert und muss durch die echte lokale ersetzt werden
Adresse. Überprüfen Sie sowohl die Lebendigkeit als auch die Bereitstellungsbereitschaft:

```bash
curl http://SERVER:9380/api/health
curl http://SERVER:9380/api/readiness
```

Die GitHub-URL wird mit der ersten öffentlichen Veröffentlichung verfügbar. Vorher,
Nutzen Sie das von der Amturo UG bereitgestellte Quellarchiv.

### Veröffentlichtes GHCR-Bild

Nachdem das erste öffentliche Tag existiert, kann eine normale Haushaltsinstallation ziehen
das signierte Bild, ohne es lokal zu erstellen:

```bash
cp .env.example .env
openssl rand -hex 32
```

Platzieren Sie den generierten Wert in `.env` als `APP_SECRET_KEY` und starten Sie dann:

```bash
docker compose -f docker-compose.release.yml pull
docker compose -f docker-compose.release.yml up -d
```

`VORRIO_VERSION` wählt das versionierte Tag aus. Pinne einen unveränderlichen Digest für a
langlebige Produktionsinstallation und überprüfen Sie deren Signatur wie in beschrieben
[Veröffentlichungs- und Upgrade-Richtlinie](RELEASES.md).

## Portainer

Erstellen Sie einen Stack aus `stack.yml`, legen Sie `APP_SECRET_KEY` in der Stack-Umgebung fest.
und einsetzen. Lassen Sie `APP_PASSWORD` leer, um die browserbasierte Ersteinrichtung zu verwenden.
`VORRIO_IMAGE` kann ein versioniertes Tag oder einen unveränderlichen Digest auswählen;
`VORRIO_DATA_VOLUME` behält ein ausgewähltes benanntes Volume über Stapelaktualisierungen hinweg bei.

## Reverse-Proxy und HTTPS

Kamerazugriff und PWA-Installation funktionieren am zuverlässigsten über HTTPS. Leiten Sie eins weiter
Hostname zum Container-Port `8080`, ersetzen Sie nicht vertrauenswürdige weitergeleitete Header und legen Sie Folgendes fest:

```env
DEPLOYMENT_PROFILE=private_https
PUBLIC_URL=https://vorrio.example.com
TRUSTED_HOSTS=vorrio.example.com
FORWARDED_ALLOW_IPS=192.0.2.20
ALLOWED_ORIGINS=https://vorrio.example.com
SESSION_HTTPS_ONLY=true
```

Schließen Sie die Ersteinrichtung in einem vertrauenswürdigen Netzwerk ab, bevor Sie eine Route veröffentlichen.
Version 0.8.18 unterstützt geschütztes öffentliches HTTPS, privates VPN/HTTPS bleibt jedoch bestehen
bevorzugtes Haushaltsprofil. Der öffentliche Datenverkehr bleibt bis zum Abschluss HTTP 503
Der Vertrag läuft und `PUBLIC_EXPOSURE_ACKNOWLEDGED=true` wird bewusst gesetzt.
Die genauen Profile und Prüfungen sind in dokumentiert
[Bereitstellungsprofile und URLs](DEPLOYMENT-PROFILES.md) und
[Sicherheitsüberprüfung für den externen Zugriff](EXTERNAL-ACCESS-SECURITY-REVIEW.md).
Lesen Sie nach der Bereitstellung vorher [Automatisierungs-API-Tokens](AUTOMATION-TOKENS.md)
Anschließen von Home Assistant oder einer Scannerstation und
[Web-Push-Benachrichtigungen](NOTIFICATIONS.md), bevor Sie Bestandsbenachrichtigungen aktivieren.

Das Frontend verwendet relative API-URLs gleichen Ursprungs. Ein anderer öffentlicher Hostname
erfordert keinen Umbau von Vorrio. Hosten Sie es nicht unter einem entfernten Pfadpräfix
wie zum Beispiel `/vorrio`; Verwenden Sie einen dedizierten Hostnamen.

### Privates LAN HTTPS für Kameratests

Ein gepflegter Reverse-Proxy kann ein internes Zertifikat für einen privaten Benutzer ausstellen
Hostnamen und leiten Sie ihn an Vorrio weiter. Installieren Sie die Stammzertifizierungsstelle des Proxys nur auf dem
Haushaltsgeräte, die dieser Installation vertrauen sollten. Der Hostname muss in sein
`TRUSTED_HOSTS`, das Proxy-Netzwerk in `FORWARDED_ALLOW_IPS` und das genaue HTTPS
Ursprung in `ALLOWED_ORIGINS`.

Dies eignet sich für ein privates LAN oder VPN. Es ist kein Ersatz dafür
Sicherheitstor für Internet-Exposition. Bevorzugen Sie einen stabilen Hostnamen. lokale IPs ändern
oder temporäre Testnamen erstellen später einen neuen Browser-Ursprung und eine neue Passkey-Identität.

### Mobile und installierte PWA

Öffnen Sie die kanonische HTTPS-Adresse in Safari oder Chrome und verwenden Sie die der Plattform
Aktion **Zum Startbildschirm hinzufügen**. Vorrio behält den gleichen Ursprung und die gleiche Sitzung bei
Standalone-Modus. Mobile Steuerelemente verwenden eine iOS-sichere Fokusgröße und behalten den Pinch-Zoom bei
und respektieren Sie die dynamische Browserhöhe sowie sichere Bereiche oben/unten.

Führen Sie `make pwa-check` aus, nachdem Sie die Viewport-Metadaten, das Manifest und global geändert haben
Layout- oder Formularstile. Die Prüfung validiert auch die Registrierung von Servicemitarbeitern und
dass das Installationssymbol ein quadratisches PNG mit mindestens 512 Pixeln bleibt.

Nach einer erfolgreichen Anmeldung kann die installierte PWA ihre zwischengespeicherte Shell erneut öffnen
Der Server ist nicht verfügbar und die Barcodes der Pakete werden lokal in die Warteschlange gestellt. Dies ist kein
Vollständige Offline-Kopie: Quittungen, Katalog, Lagerbestand und Authentifizierungsgeheimnisse sind nicht vorhanden
zwischengespeichert, und jeder in der Warteschlange befindliche Scan erfordert weiterhin eine serverseitige Auflösung und ist normal
Bestätigung nach erneuter Verbindung.

## Update

1. Lesen Sie `CHANGELOG.md` und die Migrationshinweise.
2. Sichern Sie `/data`.
3. Ziehen oder erstellen Sie die neue angeheftete Version.
4. Erstellen Sie den Container neu, ohne das Volume zu löschen.
5. Überprüfen Sie `/api/health`, `/api/readiness`, `/docs` und die PWA.

Schemamigrationen werden beim Start idempotent ausgeführt. Niemals gegen den einzigen herabstufen
Kopie einer migrierten Datenbank; Stellen Sie stattdessen das passende Backup wieder her.

Vorrio ersetzt nicht stillschweigend seinen eigenen Container. Wählen Sie eine angeheftete Version oder
Digest, sichern Sie `/data`, ziehen Sie das neue Image und erstellen Sie den Container neu. Wenn die
Wenn Änderungen an der Anwendungsversion ausgeführt werden, erhält jedes Konto die neue Version
Highlights einmal nach dem Login. Die Bestätigung wird also serverseitig gespeichert
nicht in jedem Browser wiederholen. **Einstellungen → Hilfe & Version** kann die erneut öffnen
Aktuelle Hinweise und die Produktvorstellung sind jederzeit einsehbar. Das Tag `latest` kann sein
Wird zur Bewertung verwendet, eine angeheftete Version bleibt jedoch der empfohlene Haushalt
Upgrade-Pfad, da er die Rollback-Vorbereitung und die Überprüfung der Versionshinweise übernimmt
explizit.

Version 0.8.22 fügt `users.preferred_locale` mit einem sicheren deutschen Standard für hinzu
bestehende Konten. Haushalt, Kassenzettel, Katalog, Lagerbestand usw. werden nicht umgeschrieben.
Währungs- oder Zeitzonendaten. Jeder Account kann zwischen Deutsch und Englisch wechseln
nach dem Login; Versionshinweise, Beschreibungen des API-Token-Bereichs und zukünftiger Push
Nachrichten folgen dann dieser persönlichen Entscheidung. Eine Neuinstallation der PWA ist nicht erforderlich.

Version 0.8.23 ändert kein Haushaltsschema oder gespeicherte Produktdaten. Deutsch und
Englisch wird innerhalb desselben Bildes in inhaltsgehashte Sprachblöcke aufgeteilt;
Das ausgewählte Paket wird bei Bedarf zwischengespeichert. Öffnen Sie nach dem Upgrade jedes Konto einmal
online, bevor Sie sich offline auf eine neu ausgewählte Sprache verlassen.

Version 0.8.26 ändert kein Haushaltsschema, Authentifizierungsstatus, Katalog oder
Aktiengeschichte. Es fügt einen zweisprachigen Erklärungsdialog für die fünf Scanner hinzu
Aktionen. Es ist keine Migration oder PWA-Neuinstallation erforderlich.

Version 0.8.25 ändert kein Haushaltsschema, Authentifizierungsstatus, bestätigt
Produkte oder Lagerbestandshistorie. Es stärkt den Kamerakonsens und die Barcode-Validierung.
Vorhandene ungelöste Entwürfe bleiben so lange sichtbar, bis ein Haushalt bewusst ist
verwirft sie oder ordnet sie zu.

Version 0.8.24 ändert kein Haushaltsschema, Authentifizierungsstatus oder Speicher
Produktdaten. Es bringt die öffentliche Projektwebsite, die rechtlichen Seiten und die Community in Einklang
Routen mit der überprüften Bereitstellung wurden bereits unter `vorrio.app` bereitgestellt. Die
Das Container-Upgrade aktualisiert nur die gemeldete Version und die Versionshinweise.

Version 0.8.21 ändert nur die gepflegte HTTP-Client-Abhängigkeit, die von verwendet wird
Tests und ausgehende Konnektoren. Es fügt keine Schemamigration hinzu, schreibt keine um
Haushaltsdaten und lässt den versionierten REST-Vertrag unverändert. Danach
Containeraustausch, überprüfen Sie den konfigurierten KI-Anbieter und optional Grocy
Verbindung einmal in den Einstellungen herstellen.

Die 0.8.19-Migration fügt nur benutzerspezifisches Onboarding und Versionsbestätigung hinzu.
Benutzer, die beim ersten Start von 0.8.19 bereits vorhanden sind, werden als vertraut markiert
mit der vorherigen Schnittstelle und erhalten Sie die Versionshinweise zu 0.8.19. Abrechnungen erstellt
Nach dieser Migration erhalten Sie die dreistufige Einführung. Katalog, Quittungen,
Bestand, Bilder, Sitzungen und Connector-Einstellungen bleiben unverändert.

Die 0.8.9-Migration fügt eine Haushaltsgrenze, eine Eigentümeridentität und einen Hash hinzu
serverseitige Browsersitzungen. Ein vorhandener 0.8.8 signierter Login-Cookie wird konvertiert
auf die erste Anfrage, ohne den Browser abzumelden. Der aktuelle Passwort-Hash
wird wiederverwendet, während Produkte, Belege, Lagerbestände, Bilder und Connector-Einstellungen wiederverwendet werden
unberührt gelassen. Vervollständigen Sie unten den Namen des Eigentümers und optional eine lokale E-Mail-Adresse
**Einstellungen → Konto & Sicherheit** nach dem Upgrade.

Durch die 0.8.10-Migration werden einmalige Haushaltseinladungen hinzugefügt, ohne dass Änderungen vorgenommen werden
bestehende Benutzer oder Sitzungen. Speichern Sie eine eindeutige Besitzer-E-Mail, bevor Sie die erste erstellen
Einladung. Der Link läuft nach 72 Stunden ab, kann nur einmal akzeptiert werden und lässt
Der Empfänger wählt ein unabhängiges Passwort. Sobald zwei aktive Benutzer
vorhanden, das Anmeldeformular erfordert eine E-Mail-Adresse und ein Passwort. Das Sperren eines Mitglieds wird widerrufen
alle Sitzungen dieses Kontos sofort.

Die 0.8.11-Migration fügt Passkey, TOTP, Wiederherstellungscode und eine einmalige Herausforderung hinzu
Tabellen plus Authentifizierungszeit/-methode für Browsersitzungen. Vorhanden
Sitzungen bleiben gültig; Sitzungen, die älter als zehn Minuten sind, müssen den aktuellen bestätigen
Passwort vor Sicherheits-, Familien- oder Connector-Änderungen. Öffne Vorrio durch eins
Stable erlaubt HTTPS-Hostnamen, bevor ein Passkey erstellt wird. Vorhandener Katalog,
Belege, Lagerbestände und Konnektorwerte bleiben unverändert.

Bei der 0.8.12-Migration werden die API-Token-Tabelle und die Indizes hinzugefügt. Es schafft nein
Anmeldeinformationen automatisch. Vorhandene Konten, Browsersitzungen, Katalog,
Quittungen, Lagerbestände und Anschlüsse bleiben unverändert. Erstellen Sie ein Token erst nach dem
Upgrade unter **Einstellungen → Konto & Sicherheit → API-Tokens**, kopieren Sie das Rohmaterial
Geben Sie den Wert einmal ein und speichern Sie ihn als Geheimnis im Zieldienst.

Die 0.8.13-Migration fügt persönliche Benachrichtigungseinstellungen und einen verschlüsselten Browser hinzu
Abonnements, Zustandsübergangsereignisse und begrenzte Zustellungsdatensätze. Push bleibt
deaktiviert und während des Upgrades wird keine Browserberechtigung angefordert. Öffnen Sie die
Stabile private HTTPS-PWA und Opt-in pro Gerät. Der VAPID-Schlüssel wird generiert
lokal bei der ersten Verwendung der Benachrichtigungseinstellungen und verschlüsselt mit `APP_SECRET_KEY`.

Bei der 0.8.14-Migration werden die optionale Tabelle `household_budget_settings` und a hinzugefügt
Eingangsdatumsindex. Es erstellt kein Ziel automatisch und schreibt keines neu
Beleg-, Produkt-, Lager-, Einkaufs- oder Anschlusszeile. Eigentümer oder Administrator können konfigurieren
das gemeinsame EUR-Ziel später unter **Einkäufe → Budget**.

Version 0.8.15 fügt keine destruktive Schemamigration hinzu. Es beginnt stündlich
Quittungsquellen-Aufbewahrungsauswerter, fügt Datenschutz-/Betriebsendpunkte des Eigentümers hinzu und
liefert eine reaktionsfähige Operations-/Export-/Aufbewahrungs-/Löschschnittstelle. Vorhanden
Dateien verwenden die bereits konfigurierte Datenschutzregel. Überprüfen Sie die Vorschau nach dem
Upgrade; Die geplante Bereinigung wird in den ersten fünf Minuten nicht ausgeführt.

Version 0.8.16 fügt außerdem keine Datenbankmigration hinzu und ändert den Haushalt nicht
Daten. Vorhandene LAN-/Private-HTTPS-Bereitstellungen behalten ihr Profil und ihren Zugriff.
Nur ein bewusst ausgewähltes `public_https`-Profil erhält das neue Laufzeittor;
Füllen Sie die Bereitschaftscheckliste aus, bevor Sie die Bestätigung festlegen.

Die 0.7-Migration fügt `scan_drafts`, Idempotenzindizes und `opened_at` hinzu
Lagerbestände. Vorhandene Produkte, Quittungen, Barcodes oder Lagerbestände werden nicht neu geschrieben.

Die 0.7.1-Migration fügt nullbare semantische Empfangsidentitäten und Übereinstimmungsnachweise hinzu
und Quittungs-zu-Varianten-Links. Vorhandene Belegzeilen werden aufgefüllt
konservativ; Bestandsmengen und vorherige Bestätigungen werden nicht geändert.
