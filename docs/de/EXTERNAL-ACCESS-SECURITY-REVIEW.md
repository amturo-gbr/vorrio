# Sicherheitsüberprüfung des externen Zugriffs

Überprüfungsdatum: 12.08.2026
Version: 0.8.18
Geltungsbereich: Browser/PWA -> TLS-Reverse-Proxy oder Tunnel -> Uvicorn -> Vorrio REST API

## Ergebnis

Der Anwendungspfad ist für absichtliche `public_https`-Bereitstellungen zugelassen
nur, wenn jede erzwungene Bereitschaftsbedingung erfüllt ist und der Operator dies explizit angibt
setzt `PUBLIC_EXPOSURE_ACKNOWLEDGED=true`. Derzeit ein unvollständiges öffentliches Profil
gibt HTTP 503 für die PWA und API zurück; nur Lebendigkeit und die geheimnisfreie Bereitschaft
Diagnose bleiben erreichbar. Die Auswahl eines schwächeren Profils zur Umgehung dieses Tors ist möglich
keine unterstützte öffentliche Bereitstellung.

Privates VPN/HTTPS bleibt die bevorzugte Einrichtung für Haushalte, da dadurch weniger Gefährdungen entstehen
Angriffsfläche. Das Bestehen dieser Überprüfung führt nicht automatisch zur Veröffentlichung einer Route.
DNS ändern oder einen Router-Port öffnen.

## Vertrauensgrenzen überprüft

- TLS endet an einem verwalteten Proxy oder Tunnel; nur seine tatsächliche Adresse bzw
  Das Netzwerk kann weitergeleitete Header bereitstellen.
- Der ursprüngliche dedizierte Hostname bleibt erhalten und muss mit beiden übereinstimmen
  `TRUSTED_HOSTS` und das kanonische `PUBLIC_URL`.
- Cookie-authentifizierte Statusänderungen erfordern einen genauen genehmigten Ursprung in HTTPS
  Profile. Bearer-API-Clients bleiben ohne Browser-Origin nutzbar, aber nur
  auf Endpunkten mit explizitem Gültigkeitsbereich.
- Sitzungscookies sind signiert, `HttpOnly`, `SameSite=Lax` und `Secure`.
- API-Antworten sind `Cache-Control: no-store`; Browser-Antworten empfangen HSTS,
  ein restriktiver CSP, Frame-Denial, No-Sniff, No-Referrer und Opener-Isolation.
– Öffentliche Web-Push-Abonnements müssen HTTPS sein und dürfen nur global aufgelöst werden
  routbare Adressen. Es gibt lokale, private, verbindungslokale und reservierte Ziele
  abgelehnt.
- Grocy und lokale KI-Anschlüsse können absichtlich private Netzwerke erreichen, weil
  Das ist ihr selbstgehosteter Zweck. Nur ein Besitzer mit aktueller Authentifizierung
  können ihre validierten HTTP(S)-Basis-URLs ändern; eingebettete Anmeldeinformationen, Fragmente,
  Abfragezeichenfolgen und spezielle Literalziele werden abgelehnt und umgeleitet
  bleiben deaktiviert.
- Beim Hochladen von Belegen werden Byte-, Pixel-, Format- und PDF-Rendering-Grenzwerte vor jeglicher KI beibehalten
  Anbieter sieht Inhalte. Die Ausgabe- und Produktdatenbanken der Anbieter bleiben unzuverlässig,
  Überprüfen Sie die Eingaben vor dem Schreiben.

## Erzwungenes öffentliches Profil

```env
DEPLOYMENT_PROFILE=public_https
PUBLIC_URL=https://vorrio.example.com
TRUSTED_HOSTS=vorrio.example.com
ALLOWED_ORIGINS=https://vorrio.example.com
FORWARDED_ALLOW_IPS=172.20.0.0/16
SESSION_HTTPS_ONLY=true
PUBLIC_EXPOSURE_ACKNOWLEDGED=true
PUBLISHED_ADDRESS=127.0.0.1
```

`APP_SECRET_KEY` muss ebenfalls eindeutig sein und mindestens 32 Zeichen lang sein. Die veröffentlichten
Bei dem Adressbeispiel wird davon ausgegangen, dass der Reverse-Proxy auf dem Docker-Host ausgeführt wird. Wenn es läuft
Verbinden Sie in Docker beide Dienste über ein privates Docker-Netzwerk und lassen Sie das weg
Stattdessen wird ein vom Host veröffentlichter Anwendungsport verwendet.

Stellen Sie vor dem Festlegen der Bestätigung sicher, dass kein zweiter Umweg vorhanden ist
der Proxy: keine WAN-Portweiterleitung zu `9380`, keine öffentliche Host-Firewall-Regel und nein
direkt veröffentlichter Docker-Socket, Datenträger oder SQLite-Datei.

## Wiederholbare Beweise

`make check` beinhaltet `external-path-test`. Der isolierte Produktionsbildrauch
stellt ein fertiges öffentliches Profil, CSP/HSTS-, Secure/HttpOnly/SameSite-Cookies bereit,
Ablehnung vertrauenswürdiger Hosts, Ablehnung Cross-Origins, Ablehnung fehlender Herkunft für einen
authentifiziertes Cookie, No-Store-API-Antworten und deaktiviertes TRACE. Unit-Tests auch
beweisen, dass unvollständige öffentliche Profile ausfallsichere und unsichere ausgehende URLs sind
werden abgelehnt.

Im Test wurde zusätzlich ein echter Uvicorn-Container simuliert
vertrauenswürdige Reverse-Proxy-Header. Es wurde `ready` mit HSTS für das Kanonische zurückgegeben
Host und HTTP 400 für einen nicht vertrauenswürdigen Host.

## Verbleibende Betreiberpflichten

- Halten Sie den Proxy, die Containerlaufzeit und den Host auf dem neuesten Stand; Führen Sie die Image-Schwachstelle aus
  Gate bei jeder Veröffentlichung.
– Fügen Sie eine Begrenzung der Edge-Anfragerate für Internetbereitstellungen hinzu. Vorrio ist hartnäckig
  Die Drosselung einer datenschutzsicheren Quelle ist der Backstop der Anwendung und kein Ersatz
  für volumetrischen Schutz.
- Bevorzugen Sie Passkeys und aktivieren Sie TOTP/Wiederherstellungscodes vor der Remote-Nutzung. Wiederherstellung speichern
  Codes außerhalb von Vorrio und überprüfen regelmäßig Sitzungen, Token und Audit-Ereignisse.
- Sichern Sie `/data` und `APP_SECRET_KEY` separat und testen Sie die Wiederherstellung.
- Eine zukünftige öffentliche Projektveröffentlichung erfordert noch den letzten Sicherheitskontakt,
  koordinierte Offenlegungsadresse und eine unabhängige Überprüfungsrichtlinie.
