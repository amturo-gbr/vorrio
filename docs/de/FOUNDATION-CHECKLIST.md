# Foundation-Checkliste

Diese Checkliste erfasst Plattformarbeiten, die erst nach einem entdeckt werden dürfen
öffentliche Veröffentlichung.

## Ausgeliefert in 0.6.1

- kanonische URL, Trusted-Host- und Trusted-Proxy-Konfiguration;
- Sichere Cookie-Profile, CSRF/Origin-Durchsetzung und dauerhafte Anmeldung
  Drosselung durch datenschutzsicheren Quell-Fingerabdruck;
- Anforderungstext-, Bilddekomprimierungs- und PDF-Seiten-/Rendering-Limits;
- Antwortsicherheitsheader und eine Nur-Anhang-Sicherheits-/API-Prüfungsgrundlage;
- Bereitschaftsdiagnosen, die aufgrund unsicherer öffentlicher Einstellungen fehlschlagen.
- getestete Sicherung/Wiederherstellung kompletter Volumes, Überprüfung der Datenbankintegrität und a
  Geschütztes Offline-Rotationstool `APP_SECRET_KEY`.

## Ausgeliefert in 0.7.0

- explizite Idempotenzschlüssel für Paketauflösungs- und Bestätigungsmutationen;
- Local-First-Paket-Scanning mit zwischengespeicherter Herkunft und ungelöster Wiederherstellung;
- transaktionale Bestands-/Listenaktionen mit nur anfügbaren Bewegungsdatensätzen;
- reaktionsfähige Desktop-/mobile PWA-Shell und Kamerahandhabung im sicheren Kontext;
- Regressionsabdeckung auf API-Ebene für Wiederholungssicherheit und jede Scan-Aktion.

## Ausgeliefert in 0.7.1

- semantische Erkennung doppelter Empfangsbestätigungen zusätzlich zu exakten Upload-Hashes;
- erklärbare Beweise für die Produktauflösung und Fuzzy-Kandidaten, die nur zur Überprüfung verfügbar sind;
- Automatischer lokaler Abgleich zwischen bestätigten Scans und offenen Belegen;
- API für variantenbewusste Belegerfassung und Produktpreishistorie.

## Ausgeliefert in Version 0.8.0

- explizite, externe Kandidatenerkennung nur auf Rezensionsbasis mit echten Produktbildern;
- deterministische Beweise plus eingeschränkte optionale KI-Neueinstufung;
- 30-tägiges Such-Caching mit Berücksichtigung des Ratenlimits und elegantes Upstream-Fallback;
- Duplikatsichere Kandidatenbestätigung mit Herkunft, Variante und Händler
  Lernen;
- API- und Regressionsabdeckung für Erkennung, Caching und Bestätigung.

## Ausgeliefert in 0.8.1

- explizite APIs zur Produkt-, Varianten-, Barcode- und Stammdatenbearbeitung;
- optimistische Parallelität für Produkt-, Varianten- und Stammdatenformulare;
- Aliase umbenennen, Barcode-Duplikate schützen und geschützt archivieren/löschen
  Verhalten für referenzierte Katalogdaten;
- Mutations-Audit-Ereignisse katalogisieren und reaktionsfähige Editor-Abdeckung für Mobilgeräte/Desktops.

## Ausgeliefert in 0.8.2

- explizite Eröffnungs-/Zykluszählungsüberprüfung, bei der ausgelassene Produkte unberührt bleiben;
- transaktionale, versuchssichere Zählsitzungen und nur anhängende FIFO-Bewegungen;
- schreibgeschützte Grocy-Saldovorschläge mit sichtbaren nicht übereinstimmenden Produkten und Nr
  automatische Synchronisierung;
- Mobiler/Desktop-Zählungsarbeitsbereich plus API-Regressionsabdeckung für Wiederholungsversuche und
  Vorschau des No-Write-Verhaltens.

## Ausgeliefert in 0.8.3

- validierte Mindest-/Nachfüllungsregeln und eine explizite No-Write-Vorschau;
- transaktionale, wiederholsichere Listengenerierung mit einer Neubestandsprüfung;
- duplikatsichere Konvergenz zwischen Scanner und generierten Einkaufsartikeln;
- Optimistische Listenbearbeitungen, unveränderliche Generierungsentscheidungen und Einkaufsprüfung
  Veranstaltungen;
- Responsiver Listen-/Nachfüll-/Quittungsverlaufs-Arbeitsbereich plus API-Regressionsabdeckung.

## Ausgeliefert in 0.8.4

- strikte Quittungsfortsetzungszeilenbindung für Mengen- und Stückpreiszeilen;
- überprüfte Kandidatenauswahl, die bis zu zwei echte Produktbilder beibehält
  wenn Open Facts sie bereitstellt;
- Regressionsabdeckung für Schutzmaßnahmen sowohl bei der Extraktion als auch bei der Bildauswahl.
- Dokumentierte private LAN-HTTPS-Vertrauensstellung für kameragestützte PWA-Tests ohne
  Schwächung des Public-Exposure-Tors.

## Ausgeliefert in 0.8.5

- Ergebnisbasierte Überprüfung des mobilen Scanners ohne redundante Kameraoberfläche nach einem
  Code wird aufgelöst;
- alle fünf Aktionen sichtbar zusammen mit einer expliziten Mutationserklärung;
- erreichbare mobile Bestätigung für lange Kartierungs- und Bestandsdetailformulare;
- Eine Regressionsabdeckung, die beweist, dass die Identität den Bestand unberührt lässt
  Hinzufügen, Konsumieren, Öffnen und Einkaufslistenverhalten.

## Ausgeliefert in 0.8.6

- iOS-sichere Steuerelemente für mobile Formulare ohne automatischen Fokuszoom;
- Horizontale Eindämmung des Ansichtsfensters, dynamische Höhe des Ansichtsfensters und sicherer Bereich
  Unterstützung, ohne den zugänglichen Pinch-Zoom zu blockieren;
- explizite PWA-Identität, -Bereich und eigenständige iOS/Android-Metadaten;
- Automatisierte PWA-Vertragsvalidierung als Teil von `make check`.

## Ausgeliefert in 0.8.7

- schreibgeschützte Preiszusammenfassungen und Produkthistorie aus bestätigten Importen;
- normalisierte Einzelhändlergruppierung mit neuesten, niedrigsten und durchschnittlichen Beobachtungen;
- reaktionsfähige Produktsuche, Shop-Vergleich und paketbezogene Preiszeilen;
- explizite Kennzeichnung historischer Daten plus Regressionsabdeckung, die ausschließt
  ungelöste oder lediglich vorgeschlagene Wareneingangszeilen.

## Ausgeliefert in 0.8.8

- begrenzte browser-lokale Paket-Scan-Warteschlange ohne Offline-Bestandsmutationen;
- stabile Mutationsidentifikatoren, Unterdrückung von Duplikaten und versuchssichere Wiederverbindung;
- sichtbare Warteschlangenüberprüfung/-entfernung sowie Handhabung der Kapazität bei geschlossenem Fehler;
- Zwischengespeicherter PWA-Zugriff auf zuvor authentifizierte Geräte ohne Beibehaltung
  Passwörter, Cookies, Katalogdaten oder Beleginhalte im Anwendungsspeicher.
– Durch den PWA-Vertrag erzwungenes duplikatfreies Workbox-App-Shell-Precaching.

## Ausgeliefert in 0.8.9

- zusätzliche Datensätze zu Haushalten, Erstbesitzern und eingeschränkten Rollenzugehörigkeiten;
- Konvertierung gültiger Legacy-Cookies ohne Abmeldung in eine gehashte serverseitige Sitzung
  Tokens, ohne Haushaltsdomänendaten zu berühren;
- 30-tägige Sitzungen pro Browser mit datenschutzsicheren Gerätekennzeichnungen, letzter Aktivität,
  Einzelwiderruf und Abmeldung aller anderen Geräte;
- reaktionsfähige Eigentümer-/Sitzungsverwaltung sowie Migration und Multi-Geräte-API
  Regressionsabdeckung.

## Ausgeliefert in 0.8.10

- 72-stündige einmalige Einladungen mit gehashten Token und unabhängigem Lokal
  Passwörter für jedes akzeptierte Haushaltsmitglied;
- E-Mail- und Passwort-Login, wenn mehrere Benutzer aktiv sind, mit kompatibel
  Nur-Passwort-Verhalten für einen Einbenutzerhaushalt;
- Besitzer-/Administrator-/Mitglieds-/Betrachterberechtigungen werden für jede Version zentral durchgesetzt
  API-Anfrage und gespiegelt durch rollenbewusste PWA-Steuerelemente;
- Mitgliederrollen-/Blockierungsverwaltung, sofortige Sperrung und Wiederholung der Sitzung,
  Berechtigungsgrenzen- und Mehrbenutzer-Regressionsabdeckung.

## Ausgeliefert in 0.8.11

- Auffindbare WebAuthn-Passkeys, die an einen genau genehmigten HTTPS-Ursprung gebunden sind und
  stabiler Hostname der vertrauenden Seite;
- Verschlüsseltes optionales TOTP mit Verhinderung und Ablauf von Zeitschrittwiederholungen
  Herausforderungen bei der Passwort-Anmeldung;
- gehashte Einweg-Wiederherstellungscodes mit hoher Entropie, einmalige Anzeige und Prüfung
  Wiederherstellungssitzungs-/Passwort-Reset-Ablauf;
- zehnminütige Überprüfung der aktuellen Authentifizierung auf Sicherheit, Familie, Passwort,
  Connector-Setting und Mutationen aller anderen Sitzungen;
- Responsive Benutzeroberfläche für Kontosicherheit, Authentifizierungs-Audit-Ereignisse und Abschluss
  Migrations-/API-Regressionsabdeckung.

## Ausgeliefert in 0.8.12

- Vom Besitzer/Administrator verwaltete Automatisierungs-Anmeldeinformationen mit einmaliger Rohanzeige,
  Nur SHA-256-Speicherung, obligatorischer Ablauf und sofortiger Widerruf;
- sieben explizite Least-Privilege-Bereiche für Status, Katalog, Lagerbestand und Einkauf
  und Scanner-Workflows;
- Dynamische Rollendurchsetzung, Nachverfolgung der letzten Verwendung und automatische Deaktivierung, wenn a
  Erstellerkonto ist gesperrt;
- reaktionsschnelle Home Assistant-/Scanner-Voreinstellungen plus benutzerdefinierte Auswahl;
– Trägerfähige OpenAPI-Metadaten und ungültig, fehlender Gültigkeitsbereich, abgelaufen und widerrufen
  Abdeckung der Credential-Regression.

## Ausgeliefert in 0.8.13

- explizites Opt-in durch Benutzergesten und Durchsetzung des sicheren Kontexts für Web Push;
- Verschlüsselter privater VAPID-Schlüssel und Browser-Abonnementmaterial mit vollständiger
  `APP_SECRET_KEY` Rotationsabdeckung;
- persönliche Präferenzen für niedrige Lagerbestände/Ablaufdatum und Deduplizierung bei Zustandsübergängen;
- Begrenzte Zustellungsaufzeichnungen, wiederholbare vorübergehende Fehler und automatische 404/410
  Gerätesperre;
- Reaktionsfähige PWA-Steuerelemente, Push/Click-Service-Worker-Verhalten und Synchronisierung
  REST/OpenAPI/Regressionsabdeckung.

## Ausgeliefert in 0.8.14

- Gemeinsames, vom Eigentümer/Administrator verwaltetes monatliches EUR-Haushaltsziel mit Lesezugriff für
  alle Haushaltsrollen;
- Gesamtsummen nur für bestätigten Empfang, Prognose im Kalendertempo, vergleichbare Vorherige
  Zeitraum, monatliche Historie und normalisierte Filialanteile;
- Sichtbare ausstehende, fehlende Gesamt-, Währungs- und Deckungsdiagnosen statt
  stille Schätzung;
- Migration additiver Einstellungen, datenschutzsichere Prüfereignisse, reaktionsfähige Benutzeroberfläche und
  synchronisierte REST/OpenAPI/Regressionsdokumentation.

## Ausgeliefert in 0.8.15

- Portabler Besitzerexport mit Manifest/Prüfsummen, optionalen Quelldateien und
  expliziter Ausschluss von Anmeldeinformationen, Hashes und Netzwerk-Fingerabdrücken;
- Vorschau der stündlichen/manuellen Quellenaufbewahrung beschränkt auf `/data/receipts`;
- Datenschutzsichere, strukturierte HTTP-Protokolle und reaktionsfähige Besitzeroperationen/Audit-Ansicht;
- Kürzlich authentifizierte, wörtliche und doppelt bestätigte Installationslöschung mit
  Nur synthetische destruktive Regressionsabdeckung;
- Produkteinführungsreise mit Katalog, Barcode, Quittung, Lagerbestand,
  Budget, Export und Betrieb;
- Digest-gepinnte Basisbilder, Grype-Gate mit behobener Schwachstelle, CycloneDX SBOM,
  vollständige SHA-Aktionspins und vorbereitete, schlüssellose, signierte Multi-Architektur-Releases;
- Kompatible Framework-/Krypto-/Laufzeit-Upgrades nach einem echten Image-Scan plus a
  schmale, überprüfbare OpenVEX-Anweisung für den nicht erreichbaren CPython-HTML-Parser.

## Ausgeliefert in 0.8.16

- eine spezielle Überprüfung des Browsers, des Proxys, des weitergeleiteten Headers, der Anwendung und
  Grenzen für ausgehende Anfragen;
– ein erzwungenes, bei Ausfall geschlossenes öffentliches Laufzeitgatter mit explizitem Operator
  Anerkennung;
- Strengeres CSP/HSTS/API-Caching, HTTPS-Cookie-Origin-Schutz und validiert
  Anschluss-/Push-Targets;
- ein Produktionsbild-Außenpfadrauch, der in der normalen Definition von enthalten ist
  Restliche Betreiberpflichten erledigt und dokumentiert.

## Ausgeliefert in 0.8.17

- Desktop- und Narrow-Mobile-UAT für jeden primären Arbeitsplatz, auch lange
  Empfangs- und Einstellungsseiten;
- Lokale manuelle Barcode-Validierung plus normalisierte strukturierte API-Fehler
  bleiben bei Validierungsfehlern lesbar;
- Das Feedback zu zugänglichen Einstellungen wurde behoben, das nicht unter langen Formularen verschwindet.
- eine Checkliste für den öffentlichen Start, die Quellenhygiene, CI und GHCR-Sichtbarkeit abdeckt,
  Signierung, SBOM, Repository-Sicherheitseinstellungen und Überprüfung nach der Veröffentlichung;
- automatisierte lokale Dokumentations-Link- und veröffentlichungsfähige Paket-Hygiene-Gates,
  einschließlich Fail-Closed-Secret-Vorlagen und Konsistenz der Release-Version.

## Ausgeliefert in 0.8.18

- authentifizierte Kamera-/Dateiproduktbilder, normalisiert auf metadatenfreies WebP;
- Lokale Produktmedien, die in den tragbaren Export und die dauerhafte Löschung einbezogen sind;
- zentrierte Breitbilddialoge, während der mobile Workflow ein untergeordneter Arbeitsablauf bleibt;
– Katalog-Onboarding-Kopie, die angibt, ob Grocy tatsächlich aktiviert ist.

## Ausgeliefert in 0.8.19

- Leitfaden für die erste Anmeldung mit einer zusammenhängenden Quittungs-, Scan-, Lager- und Einkaufsgeschichte;
- Abschluss- und Freigabebestätigung pro Benutzer, die auf allen Geräten geteilt wird;
- einmalige Versionshinweise pro Version nach Container-Updates;
- permanent zugängliche **Hilfe & Version**-Steuerelemente in den Einstellungen;
- Export-, Lösch-, Audit-, API- und Upgrade-Dokumentation für den Erfahrungsstatus.

## Ausgeliefert in 0.8.20

– eine Betriebsmetrik, die Validierung und Sicherheit genau beschreibt
  Ablehnungen, ohne dass dies ein Scheitern der Bewerbung bedeutet;
- eine deterministische Familien-/Sicherheitsakzeptanzreise in der normalen Version
  Gate, das die Katalog-/Quittungs-/Lagerreise ergänzt;
- sofortige Weitergabe des Eigentümerprofils in die Familienübersicht;
- Bereinigen des Abmelde-/Anmeldestatus ohne veraltete Toasts oder Dialoge;
- Wiederholte Desktop- und Narrow-Mobile-Browser-Verifizierung.

## Ausgeliefert in 0.8.21

- Starlettes gepflegter `httpx2` Test-Client-Pfad ohne Warnungsunterdrückung;
- ein HTTP-Client für Tests sowie KI-, Produktdaten- und Grocy-Anfragen;
- unveränderte REST- und Persistenzverträge, verifiziert durch das vollständige Release-Gate.

## Ausgeliefert in 0.8.22

- komplette deutsche und englische PWA-Flows, Validierung, API-Fehlerdarstellung,
  Versionshinweise und Web-Push-Kopie;
- Persönliche, beibehaltene Sprachauswahl für Setup, Einladungen und Geräte;
- Lokalisierte Zahlen-/Datums-/EUR-Formatierung sowie explizite Beibehaltung des Haushalts
  Produkt-, Beleg-, Währungs- und Zeitzonendaten;
- Deutsche und englische Manifeste und Einstiegspunkte für die Projektwebsite;
- Automatische Übersetzungsabdeckung, verdächtige Kopien und lokalisierte Backend-Tests.
- Vollständiger geheimer Scan-Verlauf in CI und Tag-Releases mit angeheftetem Digest
  Scanner plus eine eng begrenzte Zulassungsliste für Dokumentationsplatzhalter;
- Durchsetzung der Entwickleridentität von Amturo UG und Ablehnung privater Artefakte und
  gängige Formate für Anmeldeinformationen;
- ein Fresh-Runner-Installationsnachweis anhand des privat signierten GHCR-Images;
- Aktuelle NPM-, Python-, Produktions-Image- und statische OWASP-Sicherheitsüberprüfungen.

## P1 – Identitätshärtung und Automatisierung

- optionaler OIDC für Installationen, die bewusst einen externen IdP wählen;
- signierte Webhooks mit Wiederholungsversuchen, Wiedergabeschutz und Zustellungsprotokollen;
- Self-Service-Anonymisierung pro Mitglied bei der Einführung von Mehrhaushaltsmietverhältnissen;
- Optimistische Parallelität, Konfliktlösung und Idempotenzabdeckung für die
  verbleibender Beleg, Einstellungen und zukünftige Offline-Mutationen;
- Persistenz von Hintergrundjobs für OCR, Importe und Benachrichtigungen.

## Vorbereitet in 0.8.23

- Lazy offizielle Sprachblöcke mit einem dedizierten Offline-Laufzeitcache;
- versionierte Sprachmanifeste und eine zentrale typisierte Registrierung;
- ein öffentliches, reines Datenpaketschema sowie positive und kontradiktorische Validierungstests;
- stabile Namensraum-Übersetzungsschlüssel mit einer CI-Obergrenze für ältere Satzschlüssel;
- ein explizites Signatur-/Index-/Kompatibilitäts-Gate, bevor Community-Pakete dies können
  jemals zur Laufzeit installiert werden.
- ein öffentlicher Übersetzungsworkflow mit Issue- und Pull-Request-Vorlagen,
  CODEOWNERS, zerstörungsfreie Paketgenerierung, wahrheitsgetreue Abschlussprüfungen und
  Unabhängige Anforderungen an die fließende Überprüfung.

## P1 – Native-Client-Voraussetzungen

- stabile API-Kompatibilität und Client-Fähigkeitserkennung;
- Autorisierungscode mit PKCE und widerrufbaren Gerätesitzungen;
- Offline-Mutationswarteschlange mit deterministischer Deduplizierung;
- nativer Lebenszyklus der Push-Registrierung und Benachrichtigungseinstellungen pro Gerät;
- Universelle Links, Android-App-Links und Passkey-Domänenzuordnung;
- Datenschutzerklärungen, zugängliche native Flows und Store-Demo-Modus.

## P2 – stabiles öffentliches Projekt

- formeller Migrationsrahmen und Downgrade-/Wiederherstellungsrichtlinie;
- PostgreSQL-Bereitstellungsprofil ohne Schwächung der SQLite-Unterstützung;
- Barrierefreiheitstests, Lokalisierung, Währungen, Zeitzonen und Einheiten;
- anonymisierte Diagnosen, die standardmäßig aktiviert und deaktiviert sind;
- Kontakt zur öffentlichen Sicherheit, Unterstützungspolitik und koordinierte Offenlegung;
- reproduzierbare Release-Pipeline, Changelog-Automatisierung und Kompatibilitätstests;
- Synthetischer Demo-Haushalt zur Dokumentation und App-Store-Überprüfung.
