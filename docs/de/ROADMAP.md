# Roadmap

## 0,6 – unabhängige Stiftung

- eigenes Produkt-, Varianten-, Barcode- und Lagerschema;
- versionierte REST-API und synchronisierte OpenAPI-Dokumentation;
- optionale Grocy-Katalogmigration und Einwegexport;
- Offene Fakten-Barcode-Suche mit Namensnennung.

## 0.6.1 – Sicherheits- und Bereitstellungsgrundlage

- dokumentierte LAN-, VPN-, öffentliche HTTPS- und Split-DNS-Bereitstellungsprofile;
- vertrauenswürdige Hosts und explizit vertrauenswürdige Proxy-Netzwerke;
- CSRF/Origin-Durchsetzung, Anmeldedrosselung und Anforderungsressourcenlimits;
- Sicherheitsheader, Bereitschaftsdiagnose und Audit-Event-Grundlage;
- Getestete Backup-/Wiederherstellungs- und sichere Secret-Rotation-Verfahren.
- dokumentiertes Produkt-Kamera- und Hardware-Scanner-Konzept, Auflösungsreihenfolge und
  Posteingang mit unbekanntem Barcode.

## 0,7 – Scanner und reaktionsfähige PWA

- prominente Produkt-Scan-Aktion für PWA-Kamera, manuelle Eingabe und
  Tastatur-Wedge-Scanner;
- Erkennungs-, Lagerbestands-, Verbrauchs-, Öffnungs- und Einkaufslisten-Scanmodi;
- Local-First-Auflösung, zwischengespeicherte Open-Facts-Anreicherung und ein ungelöster Code
  Überprüfen Sie den Posteingang.
- idempotente Scan-/Bestätigungs-API mit transaktionalen Aktien-/Listenaktionen;
- Breite Desktop-Seitenleiste/Arbeitsbereiche und kompaktes mobiles Layout, das sichere Bereiche berücksichtigt.

## 0.7.1 – gemeinsamer Produktspeicher

- erklärbare Belegübereinstimmungen aus dem gemeinsam genutzten lokalen Produktkatalog;
- Automatischer Scan-zu-Beleg-Abgleich ohne externe Textsuche;
- Produktbild und konkreter Variantenkontext bei der Bonprüfung;
- semantische Erkennung doppelter Belege über verschiedene Erfassungen hinweg;
- REST-API für die vom Beleg abgeleitete Produktpreishistorie.

## 0.8.0 – echte Produktkandidaten

- On-Demand-bildgestützte Kandidatenerkennung für ungelöste Belegzeilen;
- Speicher-/Namens-/Marken-/Verpackungsnachweise und eingeschränktes optionales KI-Ranking;
- zwischengespeicherte Upstream-Suche mit Lizenz- und Attributionsmetadaten;
- Duplikatsichere Bestätigung in lokale Produkte und Varianten.

## 0.8.1 – Katalogbearbeitung

- reaktionsschnelle Produktdetails und Bearbeitung für Haushaltsstandards;
- Varianten- und Barcode-Management mit Validierung und Referenzschutz;
- Komplette Standort-, Einheiten- und Produktgruppenauflistung, Erstellung, Umbenennung und
  geschützter Archiv-Workflow;
- Optimistische Parallelität und Katalogprüfereignisse für jede Editormutation.

## 0.8.2 – Eröffnungsbestand überprüft

- Reaktionsschneller Öffnungs- und Zykluszählungs-Workflow, bei dem ausgelassene Produkte verbleiben
  unverändert;
- explizite Alt-gegen-Zählungs-Überprüfung mit wiederholsicherem Transaktions-Commit;
- Nur-Anhang-Zählungssitzungen, Zeilen und FIFO-Bestandsbewegungen;
- schreibgeschützte Grocy-Saldenvorschau für zugeordnete Produkte, mit sichtbaren nicht abgeglichenen Produkten
  Einträge und keine stille Erstellung oder Synchronisierung.

## 0.8.3 – automatische Einkaufsliste überprüft

- Mindestbestands- und Nachfüllziele pro Produkt im Katalogeditor;
- schreibgeschützte Vorschau auf geringe Lagerbestände vor jeder Listenänderung;
- ausgewählte, wiederholsichere Generierung, die den Lagerbestand erneut prüft und offene Einträge zusammenführt;
- Responsive Mengen-, Abwicklungs- und Empfangshistorie unter **Einkäufe**.

## 0.8.4 – Quittungs- und Bildkandidatenhärtung

- Behalten Sie gedruckte PDF-Mengen-/Preisfortsetzungszeilen bei, die sofort gebunden sind
  vorhergehendes Produkt, nie in eine Nachbarzeile verschoben;
- Bewahren Sie bis zu zwei echte, bildgestützte Open-Facts-Datensätze im überprüften Dokument auf
  Drei-Kandidaten-Ergebnis auch nach optionaler KI-Rangliste.

## 0.8.5 – ergebnisorientierter mobiler Scanner

- alle fünf Scan-Aktionen ohne abgeschnittenen horizontalen Streifen sichtbar halten;
- die ausgewählte Mutation vor der Bestätigung erläutern;
- Ersetzen Sie die Erfassungsoberfläche durch die Produktbewertung nach der Erkennung.
- Halten Sie die endgültige Bestätigung über längere mobile Formulare hinweg erreichbar;
- Überprüfen Sie jede Aktion, einschließlich „Identifizieren ohne Bestandsänderung“, in der Regression
  Abdeckung.

## 0.8.6 – mobile PWA-Stabilität

- Verhindern Sie das Zoomen des iOS-Fokus in jedem bearbeitbaren Workflow.
- Beseitigung der horizontalen Verschiebung auf Dokumentebene bis hin zu schmalen Splitscreen-Größen;
- vollständige, stabile Standalone-App-Identität und Metadaten für mobile Plattformen;
- Erzwingen Sie die Regeln für Ansichtsfenster, sicheren Bereich, Servicemitarbeiter, Symbol und Barrierefreiheit
  die automatisierte PWA-Vertragsprüfung.

## 0.8.7 – privates Preiswissen

- durchsuchbare Preisverlaufsansichten, die nur auf bestätigten Empfangsimporten basieren;
- neuester, niedrigster und vorheriger Kauftrend pro lokalem Produkt;
- normalisierter historischer Store-Vergleich mit Paketkontext;
- explizite Unterscheidung zwischen Haushaltsbeobachtungen und Live-Einzelhändlerdaten.

## 0.8.8 – sicheres Offline-Scannen

- begrenzte Warteschlange auf dem Gerät für Paket-Barcode und beabsichtigte Aktion;
- stabile Idempotenzschlüssel und duplikatsichere Reconnect-Synchronisation;
- Cached-Shell-Zugriff für zuvor authentifizierte Geräte ohne Caching
  Passwörter, Sitzungen, Katalog- oder Belegdaten;
- normale Produktbewertung und explizite Bestätigung nach jedem Offline-Scan.

## 0.8.9 – Eigentümeridentität und Browsersitzungen

- additives Haushalts-, Benutzer-, Rollenmitgliedschafts- und Serversitzungsschema;
- No-Logout-Upgrade von der zuvor unterzeichneten Haushaltssitzung;
- benannter erster Eigentümer mit optionaler lokal gespeicherter E-Mail;
- ablaufende Browsersitzungen, Gerätebezeichnungen und unmittelbare individuelle oder
  Sperrung aller anderen Geräte;
- API-, Migrations- und Regressionsabdeckung für mehrere Geräte.

## 0.8.10 – Familienkonten und Berechtigungen

- zusätzliche lokale Haushaltsnutzer durch auslaufende einmalige Einladungen;
- unabhängige Passwörter und E-Mail-basierte Anmeldung, sobald mehrere Benutzer aktiv sind;
- Eigentümer-/Administrator-/Mitglieds-/Viewer-Autorisierung durch die REST-API erzwungen;
- reaktionsfähige Mitglieder-, Rollen-, Blockierungs- und Einladungsverwaltung;
- Sofortiger Sperrung der Sitzung, wenn ein Konto gesperrt wird.

## 0.8.11 – Passkeys und Kontowiederherstellung

- erkennbare WebAuthn-Passkeys mit exakter HTTPS-Ursprungs-/RP-Validierung;
- optionales verschlüsseltes TOTP und abspielsicheres Second-Factor-Login;
- gehashte Einmal-Wiederherstellungscodes mit Wiederherstellungssitzungen zum Zurücksetzen des Passworts;
- Schutz vor aktueller Authentifizierung für Sicherheits-, Familien- und Connector-Änderungen;
- Reaktionsschnelle Kontosicherheitskontrollen und vollständige REST/OpenAPI-Abdeckung.

## 0.8.12 – Automatisierungstoken mit Gültigkeitsbereich

- Nur Hash, ablaufende Inhaberanmeldeinformationen mit einmaliger Rohanzeige;
- explizite Lese-/Schreibbereiche für Status, Katalog, Lagerbestand, Einkauf und Scans;
- Home Assistant- und Handscanner-Voreinstellungen sowie benutzerdefinierte Berechtigungen;
- sofortiger Widerruf, Nachverfolgung der letzten Verwendung und rollenbezogene Durchsetzung;
- Trägerbewusster OpenAPI-Vertrag, Prüfereignisse und Grenzregressionstests.

## 0.8.13 – Persönliche Bestandsbenachrichtigungen

- standardbasierter Opt-in-Web-Push für installierte HTTPS-PWA-Geräte;
- verschlüsselte Browser-Abonnements und ein lokal generierter verschlüsselter VAPID-Schlüssel;
- Persönliche Präferenzen für niedrige Lagerbestände und Ablaufdatum mit konfigurierbarem Warnfenster;
- Zustandsübergangsdeduplizierung, Bereinigung toter Geräte, Lieferprüfung und a
  sichtbare Testaktion pro Gerät;
- Service-Mitarbeiter-Benachrichtigung/Klick-Handhabung, Reaktionseinstellungen und Abschluss
  REST/OpenAPI/Regressionsabdeckung.

## 0.8.14 – Einnahmenbasiertes Haushaltsbudget

- gemeinsames optionales monatliches EUR-Ziel, verwaltet vom Eigentümer oder Administrator;
- Bestätigte monatliche Ausgaben, verbleibender Betrag und transparent
  Vorhersage im Kalendertempo;
- Vergleich am selben Tag mit dem Vormonat, Sechs-Monats-Verlauf und aktuelle Filialebenen;
- explizite Diagnose der ausstehenden, fehlenden Gesamt- und Nicht-EUR-Deckung;
- Responsive Mobil-/Desktop-Benutzeroberfläche plus vollständige REST/OpenAPI/Regressionsabdeckung.

## 0.8.15 – Startbereitschaft, Datenschutz und Release-Sicherheit

- Nur für den Eigentümer, geheimnisfreier tragbarer ZIP-Export für den Haushalt;
- automatische und manuelle Aufbewahrung der Quelldateien mit sicheren Pfadgrenzen;
- Datenschutzsichere Datenbank-, Fehler- und aktuelle Audit-Vorgangsansicht;
- kürzlich durchgeführte Authentifizierung plus doppelt bestätigte vollständige Löschung einzelner Haushalte;
- deterministischer synthetischer Startvorgang in der normalen Definition of Done;
- Digest-gepinnte Basisbilder, Grype-Scan, CycloneDX SBOM, SHA-gepinnte Aktionen und
  Vorbereitete Multi-Architektur-GHCR/Cosign-Releases.

## 0.8.16 – Sicherheitstor mit externem Zugang

- Spezielle End-to-End-Überprüfung der Browser-, Reverse-Proxy- und Anwendungsvertrauenswürdigkeit
  Grenzen;
– True Fail-Closed `public_https` Laufzeitgatter mit einem expliziten Endoperator
  Anerkennung;
- strenge kanonische Host-/Ursprungs-/Proxy-/Cookie-Prüfungen, gehärtete Browser-Header und
  No-Store-API-Antworten;
- Eingeschränkte Connector- und Web-Push-Ziele sowie ein Produktionsimage
  Rauch der externen Pfadregression.

## 0.8.17 – Veröffentlichungskandidaten-UAT und öffentliche Verpackung

- Vollständige Komplettlösung für alle primären PWAs für Desktop-/Mobilgeräte-Release-Kandidaten
  Arbeitsbereich und Überprüfungsgrenze;
- lesbares API-Validierungs-Feedback und sofortige lokale Scanner-Validierung;
- Immer sichtbare Verbindungstestergebnisse auf langen Einstellungsseiten;
- wiederholbare Quelle, Geheimnis, Dokumentation, Container und GitHub/GHCR-Start
  Checkliste.

## 0.8.18 – private Produktmedien und responsive Dialoge

- Kamera-/Datei-Produktbild-Upload mit sicherer WebP-Normalisierung;
- authentifizierte Zustellung, tragbarer Export und vollständige Löschung;
- zentrierte Desktop-Dialoge mit unveränderten mobilen Unterblättern;
- Connector-fähige Katalogführung und nicht mutierende Live-Grocy-Überprüfung.

## 0.8.19 – geführte Erstlauf- und Freigabekommunikation

- prägnante, responsive Produkteinführung nach der ersten Anmeldung jedes Kontos;
- eine übersichtliche Story vom Eingang über die Überprüfung bis zum Lager plus die Alternative zum Paket-Scannen;
- serverseitige Vervollständigung pro Benutzer, die auf allen Geräten geteilt wird;
- einmalige Highlights der aktuellen Version nach Änderungen einer installierten Version;
- manueller **Hilfe & Version**-Eintrag zum erneuten Öffnen beider Oberflächen;
- Portabler Export, Löschung, Prüfung, REST/OpenAPI und Regressionsabdeckung.

## 0.8.20 – Akzeptanz und betriebliche Klarheit

- Unterscheiden Sie abgelehnte Validierungs-/Sicherheitsaktionen von Serverausfällen im
  Ansicht „Eigentümerbetrieb“;
- deterministische Familien-/Sicherheitsfreigabereise über Onboarding, Einladungen,
  Rollen, Kontosperrung, Passkeys, TOTP, Wiederherstellung und Passwortrotation;
- sofortige Aktualisierung der Familienzusammenfassung nach Änderungen des Eigentümerprofils;
- klares, vorübergehendes UI-Feedback beim Abmelden und anschließenden Anmelden;
- Wiederholte UAT für Desktop-/mobile Browser und vollständige Release-Gate-Überprüfung.

## 0.8.21 – gepflegter HTTP-Client

- Ersetzen Sie den veralteten Test-Fallback `httpx` von Starlette durch `httpx2`.
- den gleichen gepflegten Client für KI-, Produktdaten- und Grocy-Verbindungen verwenden;
- Wiederholen Sie das komplette Release-Gate, ohne den REST- oder Datenvertrag zu ändern.

## 0.8.22 – Deutsch und Englisch

- Lokalisierung der vollständigen abgemeldeten und authentifizierten PWA sowie bekannter Fehler;
- Speichern Sie die Sprache pro Konto und wenden Sie sie auf Versionshinweise und Umfangsbeschreibungen an
  und Web-Push-Benachrichtigungen;
- Formatierung lokalisieren und Metadaten installieren, ohne Haushaltsdaten neu zu schreiben;
- Versenden Sie eine zweisprachige Projektwebsite und erzwingen Sie die Vollständigkeit der Übersetzung in CI.

## 0.8.23 – modulare Sprachgrundlage

- Integrieren Sie das kompakte deutsche Fallback und laden Sie andere offizielle Sprachkataloge
  als separate, zwischenspeicherbare PWA-Blöcke;
- Definieren Sie ein zentrales Sprachregister mit nativen Bezeichnungen, Richtung, Vertrauensstufe,
  Kompatibilitäts- und Vollständigkeitsmetadaten;
- Veröffentlichen und validieren Sie ein Community-Pack-Schema, das nur auf Daten basiert und Skripte ablehnt.
  HTML, unerwartete Dateien, unsichere Werte und geänderte Platzhalter;
- Beginnen Sie mit der Migration zu stabilen Namespace-Übersetzungsschlüsseln und verhindern Sie neue
  Satzschlüsselschuld in CI;
- Halten Sie die Installation des Laufzeitpakets deaktiviert, bis eine signierte, mit einer Prüfsumme versehene und
  Versionskompatibler Amturo-Paketindex ist verfügbar.
- Bereitstellung eines Sprachanfrageformulars, einer speziellen Pull-Request-Überprüfung, CODEOWNERS,
  Mitwirkender-Generator und dokumentierter angeforderter/Community-/offizieller Lebenszyklus.

## Nächster familientauglicher PWA-Meilenstein

- klarere Installations- und Upgrade-Pfade;
- weitere Verbesserung der Zugänglichkeit und Lokalisierung;
- Stabile API-Kompatibilität auf dem Weg zu 1.0.

Der externe Live-Preisvergleich bleibt als späterer optionaler Anschluss geparkt
Eine lizenzierte, maßgebliche Quelle kann das aktuelle Produkt, Paket, die aktuelle Branche usw. identifizieren.
Werbung und Verfügbarkeit, ohne die Haushaltsgeschichte als Marktdaten darzustellen.

## 0.9 – native mobile Clients

- gemeinsamer Capacitor 8-Arbeitsbereich für iOS und Android;
- Paketierte lokale Benutzeroberfläche mit konfigurierbarem, selbst gehostetem HTTPS-Server;
- Autorisierungscode mit PKCE und widerrufbaren Gerätesitzungen;
- nativer Kamera-/Barcode-Scan, Share-Sheet-Import und sichere Speicherung;
- Offline-Synchronisierung, Push-Benachrichtigungen und App-Links;
- TestFlight, interne Tests von Google Play und Speicherung von Datenschutzmaterial.

## 1.0 – stabile öffentliche Veröffentlichung

- dokumentierte Upgrade- und Support-Richtlinien;
- PostgreSQL-Option für größere Haushalte;
- erstes öffentliches GHCR-Bild/Tag unter Verwendung der vorbereiteten SBOM-, Herkunfts- und Signaturpipeline;
- Zugänglichkeit, Lokalisierung und vollständige Import-/Exportprüfung;
- Unabhängige Sicherheitsüberprüfungsrichtlinie und stabile API-Kompatibilitätsrichtlinie.

Das vollständige priorisierte Gate bleibt erhalten
[Stiftungscheckliste](FOUNDATION-CHECKLIST.md).

Rezepte, Aufgaben und Batterieverfolgung liegen bewusst außerhalb des Originals
Umfang. Sie können nach Abschluss des Inventarisierungsworkflows zu separaten Integrationen werden
ausgezeichnet.
