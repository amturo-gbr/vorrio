# Identitäts- und Authentifizierungsarchitektur

## Aktuelle Grenze

Version 0.8.16 hat einen expliziten Haushalt, separate lokale Benutzeridentitäten,
einmalige Einladungen, eingeschränkte Mitgliedschaften, individuell widerrufbarer Browser
Sitzungen, Passkeys, optionales TOTP, Einmal-Wiederherstellungscodes und bereichsgebunden
Automatisierungstoken. Derselbe Ursprung
Das Cookie `HttpOnly` enthält ein zufälliges Token, das von der Anwendung geschützt wird
Unterschrift. Nur sein SHA-256-Hash wird in SQLite gespeichert. Eine widerrufene, abgelaufene oder
Bei unbekanntem Token schlägt die Serverauthentifizierung sofort fehl; Nur das Ändern des UI-Status
kann es nicht wiederherstellen.

Die Anmeldung nur mit Passwort bleibt kompatibel, solange genau ein aktiver Benutzer vorhanden ist
und dieser Benutzer hat TOTP nicht aktiviert.
Nachdem das erste eingeladene Konto akzeptiert wurde, ist für die Anmeldung ein eindeutiges lokales Konto erforderlich
E-Mail und das Passwort dieses Benutzers. TOTP fügt der Passwortanmeldung einen zweiten Faktor hinzu;
Passkeys ermöglichen eine passwortlose Anmeldung. Es wird keine Wiederherstellungs-E-Mail gesendet. Wiederherstellungscodes
werden lokal erstellt, einmalig angezeigt und können so eine normale widerrufliche Sitzung erstellen
Der Benutzer kann ein vergessenes Passwort ersetzen. Zusätzlich direktes öffentliches HTTPS
erfordert jedes erzwungene externe Pfad-Gate und jeden expliziten Operator
Anerkennung; Privates VPN/HTTPS bleibt bevorzugt.

Die aktuelle Baseline wendet außerdem genaue Prüfungen auf vertrauenswürdige Hosts und eingeschränkte Proxys an
Header, Same-Origin-Validierung für Statusänderungen, dauerhafte Anmeldung pro Quelle
Drosselung, ständiger Anmeldefehlertext und nur anfügbare Überwachungsereignisse für
Authentifizierung und authentifizierte Mutationen. Quelladressen sind HMAC
vor der Lagerung werden Fingerabdrücke genommen; Rohe Client-IPs werden nicht in die Prüfung geschrieben
Tische.

Zur sicheren Offline-Paketerfassung speichert ein zuvor authentifizierter Browser eines
Nicht geheimer lokaler Hinweis, der nur das Rendern der vorab zwischengespeicherten PWA-Shell und ermöglicht
Offline-Warteschlange, während der Server nicht verfügbar ist. Der Hinweis kann eine nicht autorisieren
API-Anfrage. Die Warteschlange enthält Barcode, beabsichtigte Aktion, Zeitstempel und a
Client-Mutations-ID, aber kein Passwort, Cookie, Beleg, Katalogergebnis oder Bestand
Daten. Danach sind eine Serverauthentifizierung und die normale explizite Überprüfung erforderlich
Wiederverbindung.

## Ausgelieferte Identitätsgrundlage

Das additive Schema umfasst nun:

- `households` als zukünftiger Mieter und Verschlüsselungsgrenze;
- `users` für lokale Identitäten, unabhängige Passwort-Hashes und Lebenszyklusstatus;
- `household_memberships` mit einer Rollenbeschränkung „owner/admin/member/viewer“;
- `auth_sessions` mit einem gehashten Zufallstoken, datenschutzsicherer Gerätebezeichnung,
  Erstellungs-/Zuletzt gesehene/Ablaufzeiten, letzte Authentifizierungsmethode/-zeit und a
  Widerrufszeitstempel;
- `household_invitations` mit gehashten zufälligen einmaligen Token, Empfänger-E-Mail,
  vorgeschlagene Rolle, Ablauf und Annahme-/Widerrufsstatus;
- `webauthn_credentials` und fünfminütige einmalige Verwendung `webauthn_challenges` für
  öffentliche Schlüssel, Signaturzähler, genaue Ursprünge und Hosts der vertrauenden Seite;
- `totp_credentials` für verschlüsselte Geheimnisse und den letzten akzeptierten Zeitschritt;
- `recovery_codes` und `login_challenges`, wobei nur Roh-Hashes gespeichert werden
  Einwegwerte;
- `api_tokens` mit einem reinen Hash-zufälligen Trägergeheimnis, Ersteller-/Haushalts-Links,
  explizite Bereiche, Zeitstempel für Ablauf, letzte Verwendung und Widerruf.

Aktive Sitzungen listet die PWA unter **Einstellungen → Konto & Sicherheit** auf.
Durch das Widerrufen der aktuellen Zeile wird dieser Browser abgemeldet. Das Widerrufen einer weiteren Zeile dauert
Auswirkung auf den nächsten API-Aufruf. **Andere Geräte abmelden** bewahrt nur die
aktuelles Token. Der vollständige Benutzeragent und die Roh-Client-IP werden nicht beibehalten. Besitzer
und der Administrator kann den Haushalt auflisten; Nur der Besitzer kann Admin gewähren oder Admin ändern
Konten. Durch das Blockieren eines Mitglieds wird jede Sitzung für dieses Konto widerrufen.

## Verbleibendes Identitätsmodell

Die nächsten Identitätsstufen fügen hinzu:

- `device_authorizations` für den Native-Client-Widerruf;
– eine dem Besitzer zugewandte schreibgeschützte Ansicht des bereits persistenten `audit_events`.

Jede haushaltseigene Domaintabelle benötigt vorher eine unveränderliche `household_id`
Der Mehrhaushaltsmodus ist aktiviert. Das Filtern nur in der Benutzeroberfläche ist nicht möglich
Sicherheitsgrenze.

## Rollen

| Rolle | Beabsichtigte Berechtigungen |
|---|---|
| Eigentümer | Sicherheitseinstellungen, Mitglieder, Backups, Connectors und alle Haushaltsdaten. |
| Admin | Nicht-Administrator-Mitglieder, Katalog und normale Haushaltsabläufe; Keine Anschlüsse oder Eigentümersicherheit. |
| Mitglied | Belegprüfung/-import, Scanner, Bestandszählung und Einkaufslisten-Workflows. |
| Betrachter | Nur-Lese-Katalog, Preise, Quittungen, Lagerbestände und Einkaufszugang. |

Berechtigungen werden in der REST-API erzwungen und dort getestet. Eine Schaltfläche auszublenden ist
nur ein Usability-Maß.

## Authentifizierungsmethoden

Passkeys über WebAuthn sind aus diesem Grund die bevorzugte primäre Methode
Phishing-resistent und kann eine passwortlose Multi-Faktor-Authentifizierung bieten.
Sie erfordern HTTPS und eine stabile Relying-Party-Domäne. Vorrio überprüft das
Browserursprung gegen `ALLOWED_ORIGINS`/`PUBLIC_URL`, erfordert Benutzerüberprüfung
und speichert nur das öffentliche Ausweismaterial und den Unterschriftenzähler.

Für einfache private Installationen bleibt die Passwortanmeldung weiterhin verfügbar. TOTP ist ein
optionaler zweiter Faktor für Passwortbenutzer und lehnt die Wiederverwendung einer akzeptierten Zeit ab
Schritt. SMS ist kein Sicherheitsfaktor. Für jedes Konto können mehrere registriert werden
Hauptschlüssel. Zehn Wiederherstellungscodes mit hoher Entropie können generiert oder ersetzt werden. nur
Ihre SHA-256-Hashes bleiben erhalten und jeder Code funktioniert einmal.

Sicherheitsrelevante Mutationen akzeptieren nur eine innerhalb der authentifizierte Sitzung
letzten zehn Minuten. Bei der erneuten Bestätigung wird das aktuelle Passwort und ggf. TOTP verwendet
aktiviert, ein gültiger Authentifikator oder Wiederherstellungscode. Die Anmeldung mit dem Wiederherstellungscode erfolgt selbst
aktuelle Authentifizierung, sodass ein verlorenes Passwort sofort geändert werden kann; alles andere
Browsersitzungen werden durch diese Passwortänderung widerrufen.

### Automatisierungstoken

Eigentümer und Administrator können nach einer bestimmten Zeit ein ablaufendes Token für einen nichtmenschlichen Client erstellen
aktuelle Identitätsbestätigung. Der Rohwert wird genau einmal zurückgegeben und hat
das Formular `vor_pat_<prefix>_<secret>`; SQLite speichert nur seinen SHA-256-Hash. Der
Das sichtbare Präfix identifiziert ein bereitgestelltes Token, ohne es preiszugeben. Token verfallen
nach 1–365 Tagen, können sofort widerrufen werden und werden deaktiviert, wenn ihre
Der Ersteller oder die Mitgliedschaft ist blockiert.

Senden Sie den Wert nur als `Authorization: Bearer <token>` über HTTPS. Ein Träger
Die Anfrage greift niemals auf ein gültiges Browser-Cookie zurück, wenn das bereitgestellte Token vorhanden ist
ungültig und ein API-Token kann Identität, Einstellungen, Connector und Empfang nicht aufrufen
Upload oder direkte Katalogmutationsendpunkte. Der aktuelle Haushalt des Erstellers
Die Rolle bleibt eine zusätzliche Berechtigungsgrenze.

| Geltungsbereich | Ermöglicht |
|---|---|
| `status:read` | Instanz- und Connector-Status. |
| `catalog:read` | Produkte, Barcodes und Stammdaten. |
| `stock:read` | Produktgesamtsummen und Zählhistorie auf Lager zählen. |
| `shopping:read` | Einkaufsliste und Vorschau auf geringe Lagerbestände. |
| `shopping:write` | Überprüfte Listengenerierung und Aktualisierungen von Listenelementen. |
| `scans:read` | Scannen Sie Entwürfe und den Posteingang mit ungelöstem Code. |
| `scans:write` | Scan-Entwürfe auflösen, bearbeiten, bestätigen oder verwerfen. |

Die PWA bietet eine schreibgeschützte Home Assistant-Voreinstellung und eine Scanner-Voreinstellung. Benutzerdefiniert
Die Bereichsauswahl ist für andere lokale Dienste verfügbar. OpenAPI markiert jeden
Trägerfähiger Betrieb mit `x-vorrio-required-scope`.

Optional kann OIDC später mit Authentik oder einem anderen standardkonformen Gerät verbunden werden
Identitätsanbieter. Lokale Konten werden weiterhin unterstützt, also ein selbstgehosteter Haushalt
kann sich nicht selbst aussperren, nur weil ein externer Identitätsdienst ausgefallen ist.

## Migration vom Haushaltspasswort

Bei einer bestehenden Installation verwendet Vorrio den aktuellen Passwort-Hash wieder und erstellt ihn
genau eine Haushalts-/Eigentümermitgliedschaft. Ein gültiges signiertes 0.8.8-Cookie wird aktualisiert
bei seiner ersten Anfrage vorhanden: Der Browser erhält ein zufälliges Sitzungstoken und
Die Datenbank speichert nur ihren Hash. Katalog, Lagerbestand, Quittungen, Dateien und Connector
Einstellungen werden nicht neu geschrieben.

Der Eigentümer kann weiterarbeiten, bevor er dem migrierten Profil einen Namen gibt. Eine hervorgehobene
Die Einstellungskarte fordert einen Anzeigenamen und optional eine lokale E-Mail-Adresse an. Speichern Sie es Markierungen
Der Bootstrap ist abgeschlossen. Dadurch wird vermieden, dass ein unbeaufsichtigtes Upgrade gesperrt wird
Haushalt. Bei Neuinstallationen wird der Besitzername während der Erstinstallation erfasst.

Die 0.8.11-Migration fügt Authentifikator- und Challenge-Tabellen sowie zwei Additive hinzu
Sitzungsfelder. Vorhandene Sitzungen werden ab dem Zeitpunkt ihrer Erstellung aufgefüllt.
Das heißt, ein älterer, noch gültiger Browser bleibt angemeldet, muss dies jedoch bestätigen
Passwort vor einer sensiblen Änderung. Kein Katalog, keine Quittung, kein Lagerbestand oder Stecker
Datensatz wird neu geschrieben.

Bei der 0.8.12-Migration werden nur die Tabelle und die Indizes `api_tokens` hinzugefügt. Es schafft nein
Token automatisch und schreibt Benutzer, Sitzungen oder Haushaltsdomänen nicht neu
Daten.

Die 0.8.13-Migration fügt persönliche Benachrichtigungseinstellungen und verschlüsseltes Push hinzu
Geräte, Zustandsübergangsereignisse und begrenzte Lieferdatensätze. Push bleibt
deaktiviert, bis sich ein Benutzer über eine HTTPS-PWA anmeldet. Das gleiche gehütete Geheimnis
Durch die Rotation werden VAPID-, TOTP-, Connector- und Push-Abonnement-Geheimnisse neu verschlüsselt.

Für Mitgliedereinladungen werden 72-Stunden-Einmallinks verwendet. Ihr roher Zufallstoken ist
wird nur in der Erstellungsantwort angezeigt, während die Datenbank nur einen SHA-256 speichert
Hash. Der Empfänger wählt bei der Annahme ein eigenständiges Passwort. SMTP
kann später ein optionaler Übermittlungsmechanismus sein, ist aber nicht erforderlich.

## Sicherheitskontrollen für die Internetexposition

- Permanente, datenschutzsichere Quell-Login-Drosselung plus Edge-Rate-Limit
  Anforderung an direkte Internet-Bereitstellungen;
- Ständige Authentifizierungsfehlermeldungen und Protokollierung von Sicherheitsereignissen (Baseline).
  versandt);
- CSRF/Origin-Prüfungen auf Cookie-authentifizierte Statusänderungen (ausgeliefert);
- Sichere, HttpOnly- und entsprechende SameSite-Cookies über HTTPS;
- Trusted-Host- und Trusted-Proxy-Durchsetzung (im Lieferumfang enthalten);
- Sitzungsliste, datenschutzsichere Gerätenamen, Abmeldung aller anderen und individuell
  Widerruf (ausgeliefert in 0.8.9);
- Zusätzliche Benutzer, einmalige Einladungen und API-erzwungene Rollenberechtigungen
  (ausgeliefert in 0.8.10);
- Passkeys, optionales TOTP, einmalige Wiederherstellungscodes und getestete Wiederherstellungsanmeldung
  (ausgeliefert in 0.8.11);
- Aktuelle Authentifizierungsprüfungen für Sicherheits-, Familien- und Connector-Änderungen
  (ausgeliefert in 0.8.11; Offline-Backup-Verwaltung bleibt betriebsbereit);
- bereichsbezogene, ablaufende API-Tokens anstelle der gemeinsamen Nutzung einer menschlichen Sitzung (im Lieferumfang enthalten).
  0,8,12);
- Prüfaufzeichnungen für Anmeldung, MFA, Mitgliedschaft, Berechtigung und Token-Änderungen;
- Validierung des Upload-Typs, Dekomprimierungsgrenzen und isolierte PDF-/Bildanalyse;
- Abhängigkeits-, Container- und Release-Sicherheitsüberprüfungen.

Das komplette Pflichtprofil, Testnachweise und restliche Betreiberpflichten live
in [Sicherheitsüberprüfung für externen Zugriff](EXTERNAL-ACCESS-SECURITY-REVIEW.md).

Passwörter sollten auf eine aktuelle speicherintensive Passwort-Hashing-Richtlinie migriert werden
ohne vorhandene Verschlüsselungs-Hashes ungültig zu machen: Überprüfen Sie den alten Hash einmal und
Wiederholen Sie es bei erfolgreicher Anmeldung.
