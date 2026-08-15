# Konfiguration

## Umgebungsvariablen

| Variable | Erforderlich | Standard | Zweck |
|---|---:|---|---|
| `VORRIO_VERSION` | nur Verfassen freigeben | `0.8.26` | Versioniertes GHCR-Tag, ausgewählt von `docker-compose.release.yml`. |
| `APP_SECRET_KEY` | ja | Entwicklungs-Fallback | Verschlüsselt Anbieter-/Connector-, TOTP-, VAPID- und Push-Abonnement-Geheimnisse und signiert das Cookie mit einem zufälligen Serversitzungstoken. |
| `APP_PASSWORD` | nein | leer | Optional vorkonfiguriertes Haushaltspasswort; empty ermöglicht die erstmalige Einrichtung. |
| `DEPLOYMENT_PROFILE` | nein | `lan` | Wählt `lan`, `private_https` oder die geschützte `public_https`-Richtlinie aus. |
| `PUBLIC_URL` | HTTPS-Profile | leer | Kanonischer Ursprung für generierte Links und Ursprungsvalidierung; kein Pfadpräfix. |
| `TRUSTED_HOSTS` | externer Zugriff | `*` | Durch Kommas getrennte HTTP-Hostnamen. Der Platzhalter gilt nur für LAN. |
| `ALLOWED_ORIGINS` | Passschlüssel/HTTPS | leer | Genaue Browser-Ursprünge, die von den CSRF-Schutz- und Passkey-Zeremonien akzeptiert werden; aktiviert kein Platzhalter-CORS. |
| `FORWARDED_ALLOW_IPS` | hinter Proxy | `127.0.0.1` | Durch Kommas getrennte Proxy-IPs/Netzwerke dürfen `X-Forwarded-*` bereitstellen. Verwenden Sie `*` niemals für einen exponierten Dienst. |
| `SESSION_HTTPS_ONLY` | HTTPS-Profile | `false` | Fügt Sitzungscookies das Secure-Flag hinzu. |
| `PUBLIC_EXPOSURE_ACKNOWLEDGED` | öffentliches HTTPS | `false` | Ausdrückliche abschließende Anerkennung; Der öffentliche Anwendungsverkehr bleibt HTTP 503, bis auch alle anderen Sicherheitsbedingungen erfüllt sind. |
| `PUBLISHED_ADDRESS` | nein | `0.0.0.0` | Für den Compose-Port verwendete Hostadresse `9380`; Verwenden Sie `127.0.0.1` mit einem Host-Proxy oder einem privaten Docker-Netzwerk ohne veröffentlichten App-Port. |
| `VORRIO_DATA_VOLUME` | Veröffentlichung Compose/Portainer | `vorrio_data` | Benanntes Docker-Volume, das für persistente Anwendungsdaten verwendet wird. |
| `MAX_UPLOAD_MB` | nein | `12` | Maximale Quittungsbild- oder PDF-Größe. |
| `MAX_REQUEST_MB` | nein | `13` | Maximal vollständige HTTP-Anfrage inklusive mehrteiligem Overhead. |
| `MAX_IMAGE_MEGAPIXELS` | nein | `40` | Pixellimit vor der Bildanalyse überprüft. |
| `RECEIPT_RETENTION_DAYS` | nein | `7` | Standardmäßiger Zeitraum für die Aufbewahrung der Belegdatei. |
| `LOGIN_MAX_FAILURES` | nein | `5` | Fehlgeschlagene Anmeldungen pro datenschutzsicherem Quellenfingerabdruck im Zeitfenster zulässig. |
| `LOGIN_WINDOW_SECONDS` | nein | `900` | Anmeldedrosselungsfenster und Wiederholungsintervall. |
| `WEB_PUSH_SUBJECT` | nein | `mailto:admin@vorrio.local` | VAPID-Kontaktanspruch; Verwenden Sie einen echten `mailto:`- oder HTTPS-Kontakt für ein verteiltes Produktionsimage. |
| `NOTIFICATION_CHECK_SECONDS` | nein | `900` | Bewertungsintervall für niedrigen Lagerbestand/Ablauf, beschränkt auf 60–86400 Sekunden. |
| `DATA_DIR` | Container-verwaltet | `/data` | Datenbank und Speicherort für einbehaltene Quittungen. |
| `TZ` | nein | einsatzspezifisch | Containerzeitzone, die für Betriebsprotokolle verwendet wird. |

Übergeben Sie keine Anbieter- oder Grocy-Schlüssel über festgeschriebene Compose-Dateien. Geben Sie sie ein
über den authentifizierten Einstellungsbildschirm; Sie werden vor der Speicherung verschlüsselt.

Diese Bereitstellungsvariablen werden in 0.8.16 erzwungen. Überprüfen Sie anschließend `/api/readiness`
jede Hostnamen-, TLS- oder Reverse-Proxy-Änderung. Der Endpunkt stellt nur sichere Informationen bereit
Bestehen/Warnen/Fehlgeschlagen-Diagnose, nicht konfigurierte Geheimnisse oder Netzwerklisten. Siehe
[Bereitstellungsprofile und URLs](DEPLOYMENT-PROFILES.md).
Die Bestätigung und die vollständige Checkliste sind in dokumentiert
[Sicherheitsüberprüfung für externen Zugriff](EXTERNAL-ACCESS-SECURITY-REVIEW.md).

Die authentifizierte Datenschutzeinstellung steuert sowohl neue als auch geplante Uploads
Quelldatei-Evaluator. Der Prozess wartet nach dem Start fünf Minuten und wird dann ausgeführt
stündlich. Eigentümer können eine Vorschau anzeigen und dieselbe Regel sofort anwenden. es gibt keine
Separater Cron oder Umgebungsvariable, um die Synchronisierung zu gewährleisten.

## Analyseanbieter

Wählen Sie in den Einstellungen den Anbieter, die Basis-URL, das visionfähige Modell und den API-Schlüssel aus.
Ollama kann ohne Schlüssel laufen. Siehe [KI-Anbieter](AI-PROVIDERS.md).

Empfangsmedien verlassen den Server nur, wenn ein Remote-Anbieter ausgewählt wird. PDF
Das Rendering und die Extraktion des eingebetteten Texts erfolgen zunächst lokal.

## Schnittstellensprache

Es gibt keine bereitstellungsweite Sprachumgebungsvariable. Deutsch oder Englisch
wird pro Konto ausgewählt und in der lokalen Datenbank gespeichert. Beides offiziell
Nur-Daten-Pakete werden im gleichen Image ausgeliefert; Die PWA lädt die ausgewählten Daten und speichert sie zwischen
Katalog auf Anfrage. Stellen Sie vor der Anmeldung den Browser und die letzte lokale Auswahl bereit
Ausgangssprache; Nach der Anmeldung hat die Kontoeinstellung Vorrang. Siehe
[Lokalisierung](LOCALIZATION.md).

## Web-Push

Push ist deaktiviert, bis jeder Benutzer explizit ein HTTPS-PWA-Gerät aktiviert. Nein
Es ist ein SMTP- oder gehostetes Benachrichtigungskonto erforderlich. Siehe
[Web-Push-Benachrichtigungen](NOTIFICATIONS.md) für den Gerätefluss, Ereignisregeln und
Lebenszyklus des verschlüsselten Schlüssels.

## Haushaltsbudget

Das gemeinsame monatliche EUR-Ziel sind Anwendungsdaten und nicht eine Umgebung
variabel. Der Eigentümer oder Administrator konfiguriert es unter **Einkäufe → Budget**. Verlasse es
Unset zeigt weiterhin den bestätigten Ausgabenverlauf an. Siehe [Haushaltsbudget](BUDGET.md)
für Zählung, Berechtigungen und Prognosegrenzen.

## Grocy-Anschluss

Grocy ist bei Neuinstallationen deaktiviert. Für die Aktivierung ist eine URL erforderlich und normal
Benutzer-API-Schlüssel. Der Connector unterstützt die Katalogmigration und den unidirektionalen Export; es
wird nicht zu Vorrios Quelle der Wahrheit.

Durch das Deaktivieren des Connectors bleiben der verschlüsselte Schlüssel und die Zuordnungen erhalten, sodass dies möglich ist
ohne Datenverlust wieder aktiviert werden.

## Privatsphäre des Empfangs

Aktivieren Sie „Nach der Analyse löschen“, um die hochgeladene Quelle sofort danach zu entfernen
Strukturierte Extraktion. Analysierte Belegdaten, Überprüfungsentscheidungen und Lagerbestände
Bewegungen bleiben in SQLite.
