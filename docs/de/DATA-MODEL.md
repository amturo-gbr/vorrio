# Datenmodell

## Katalog

- `catalog_products`: generische Haushaltskonzepte wie Milch oder Kaffee,
  inklusive optionaler Mindestbestände und Nachfüllzielmengen;
- `catalog_product_variants`: konkrete Marken- und Paketkombinationen;
- `catalog_barcodes`: EAN-, UPC- oder andere an Varianten angehängte Codes;
- `catalog_locations`: Speisekammer, Kühlschrank, Gefrierschrank und benutzerdefinierte Plätze;
- `catalog_quantity_units`: Lager- und Kaufeinheiten;
- `catalog_product_groups`: Haushaltskategorien;
- `catalog_aliases` und `catalog_product_mappings`: bestätigter Empfangstext;
- `catalog_external_refs`: Quelle, Lizenz, Namensnennung und zwischengespeicherter Barcode oder
  Produktkandidaten-Metadaten. Suchabfrage-Cache-Datensätze verwenden einen gehashten Kontext
  Schlüssel und enthalten kein Provider-Geheimnis.

Bilder lokaler Haushaltsprodukte werden unter `/data/product-images` als Ganzes angezeigt
Metadatenfreies WebP pro Produkt. `catalog_products.image_url` speichert entweder seine
authentifizierte API-Route oder eine optionale externe HTTP(S)-Adresse. Die Dateien sind
Teil von Volumensicherungen und tragbaren Haushaltsexporten.

Katalogzeilen behalten `created_at` und `updated_at` bei. Produkt-, Varianten- und Stammdaten
Formulare übermitteln den letzten beobachteten Aktualisierungszeitstempel; Ein veralteter Schreibvorgang wird abgelehnt.
Durch das Umbenennen eines Produkts wird stattdessen der frühere normalisierte Name zu `catalog_aliases` hinzugefügt
früheres Empfangswissen zu verlieren. Stammdaten verwenden `active=0` als Archiv,
und referenzierte Varianten bleiben vor Löschung geschützt.

## Aktie

- `stock_lots`: aktuelle Menge, Standort, Preis, optionales Mindesthaltbarkeitsdatum und
  expliziter `opened_at` Zeitstempel;
- `stock_movements`: Nur-Anhang-Kauf, Verbrauch, Korrektur und Übertragung
  Tagebuch;
- `stock_count_sessions`: Retry-Safe-Header für ein überprüftes Handbuch oder
  Grocy-unterstützte Zählung;
- `stock_count_lines`: unveränderliche vorherige, gezählte und Differenzwerte plus
  ausgewählter Standort, Variante, Mindesthaltbarkeitsdatum und erstellte Bewegungsanzahl;
- `shopping_list_items`: offene oder abgeschlossene explizite zukünftige Käufe;
- `shopping_generation_runs`: eindeutige wiederholsichere Header für eine bestätigte
  Vorschlag für Mindestbestände;
- `shopping_generation_items`: unveränderliche aktuelle/minimum/target/shortage-Werte
  und die erstellte, aktualisierte, unveränderte oder übersprungene Aktion pro ausgewähltem Produkt.

Ein bestätigter Wareneingangsartikel kann höchstens ein Lagerlos erstellen. Korrekturen sollten
Bewegungen schaffen, statt die Geschichte auszulöschen. Eine Zählung ändert sich nur explizit
eingereichte Produkte. Steigerungen schaffen viel und Bewegung; verringert den Verbrauch
vorhandene Lose im FIFO und kann mehrere Bewegungen erzeugen. Die einzigartige Client-Mutation
Der Bezeichner gibt bei einem Wiederholungsversuch die ursprüngliche Zählsitzung zurück.

Ein Nachfüllziel von Null deaktiviert automatische Vorschläge. Ein aktiviertes Ziel muss
größer sein als das Minimum. Die Generierung berechnet die aktuellen Lossummen neu
seine Transaktion und erstellt oder erhöht nur dann einen offenen Posten, wenn das Produkt verfügbar ist
immer noch förderfähig. Vorhandene größere Mengen bleiben erhalten. Vervollständigen einer Liste
item ist ein geprüfter Zustandsübergang; Die Geschichte der Generationen wird nicht neu geschrieben.

## Quittungen

- `receipts`: Händler, Filiale, Datum, Währung, Summen, exakter Datei-Hash und
  konservativer semantischer Quittungsfingerabdruck;
- `receipt_items`: erkannte Zeile, bestätigter Produkt-/Variantenlink, strukturiert
  Übereinstimmungsnachweis, Connector-Link und Importstatus;
- `import_runs`: überprüfbares Ergebnis jedes Commit-Versuchs.

## Paketscans

`scan_drafts` speichert den rohen und normalisierten Code, die Symbologie, den ausgewählten Modus,
Lösungsquelle, optionales lokales Produkt/Variante, externer Vorschlag,
Upstream-Fehler, Status und Zeitstempel. Auflösungs- und Bestätigungsschlüssel vorhanden
teilweise eindeutige Indizes. Ein bestätigter Entwurf speichert sein Aktionsergebnis, sodass ein erneuter Versuch möglich ist
kann genau die ursprüngliche Antwort zurückgeben.

Bekannte Codes verweisen direkt auf die bestehende Variante. Nur extern und unbekannt
Codes bleiben `unresolved`, bis ein Haushaltsmitglied ein Produkt zuordnet oder erstellt.
Beim Verwerfen handelt es sich eher um einen Zustandsübergang als um ein Löschen, das den Verlauf zerstört.

Die Offline-Paketwarteschlange ist bewusst keine Servertabelle. Es ist begrenzt
Browser-lokaler Status, der nur Code, beabsichtigten Modus, Zeitstempel und das enthält
Idempotenzschlüssel auflösen. Eine Zeile erreicht `scan_drafts` erst nach der Authentifizierung
Synchronisierung wiederherstellen; Bestands- und Listenmutationen erfordern noch einen späteren Zeitpunkt
ausdrückliche Bestätigung.

## Einstellungen, Sicherheit und Identitäten

Version 0.8.16 unterstützt einen Haushalt, separate lokale Konten und verschlüsselt
Verbindungseinstellungen. `households` identifiziert die Mandantengrenze. `users`
enthält den lokalen Anzeigenamen, eine eindeutige optionale E-Mail-Adresse und ein unabhängiges Passwort
Hash- und Lebenszyklus-Flags.
`household_memberships` verknüpft diese Identität mit einer Einschränkung mit dem Haushalt
Besitzer-/Administrator-/Mitglieds-/Betrachterrolle. Die API erzwingt diese Mitgliedschaften bei jedem
versionierte Anfrage.

`household_invitations` speichert nur den SHA-256-Hash eines zufälligen Tokens zusammen
mit Haushalt, Einladender, E-Mail/Name des Empfängers, vorgeschlagene Rolle, Ablaufdatum und
Annahme-/Widerrufsstatus. Durch die Akzeptanz entstehen Benutzer und Mitgliedschaft in einem
Transaktion und verbraucht den Token. Der Roh-Token kann niemals wiederhergestellt werden
Datenbank.

`auth_sessions` enthält eine öffentliche Sitzungskennung, den SHA-256-Hash des Zufalls
Browser-Token, Haushalts-/Benutzer-Links, eine abgeleitete datenschutzsichere Gerätebezeichnung,
Erstellungs-/Zuletzt gesehene/Ablauf-Zeitstempel, letzte Authentifizierungszeit/-methode und
optionale Widerrufsfrist. Der rohe Token
existiert nur innerhalb des signierten Browser-Cookies `HttpOnly`. Kein vollständiger Benutzeragent oder
Die rohe IP-Adresse wird gespeichert.

`webauthn_credentials` speichert öffentliche Passschlüssel, Signaturzähler und Backups
Status und vom Benutzer gewählte Labels. `webauthn_challenges` bindet jede Registrierung bzw
Anmeldeversuch bei einer einmaligen Herausforderung, genauer Herkunft, Hostname der vertrauenden Seite und
Ablauf von fünf Minuten. Kein Passkey-privater Schlüssel gelangt in Vorrio.

`totp_credentials` speichert das mit `APP_SECRET_KEY` verschlüsselte gemeinsame Geheimnis.
Aktivieren Sie den Status und den letzten akzeptierten Zeitschritt, um die Wiedergabe abzulehnen. `recovery_codes`
Speichert nur SHA-256-Hashes und verwendet Zeitstempel. `login_challenges` enthält gehasht,
kurzlebige Fortsetzungstoken zwischen Passwort- und Zweitfaktorprüfungen.

`api_tokens` speichert nur den SHA-256-Hash und das nicht geheime Präfix jedes Zufalls
Automatisierungsberechtigung zusammen mit ihrem Ersteller, Haushalt, expliziten Bereichen,
Zeitstempel für Ablauf, letzte Verwendung und Widerruf. Rohe Trägerwerte existieren nur im
eine Schöpfungsantwort.

`notification_preferences` speichert den Opt-in-Schalter jedes Benutzers, geringer Lagerbestand/Ablauf
Auswahlmöglichkeiten und Warnfenster. `push_subscriptions` speichert nur einen Endpunkt-Hash
für den Abgleich plus das vollständige Browser-Abonnement, verschlüsselt mit
`APP_SECRET_KEY`. `notification_events` zeichnet den aktiven/gelösten Zustand auf
Übergänge, sodass regelmäßige Überprüfungen keinen unveränderten Zustand spammen können.
`notification_deliveries` speichert 90 Tage lang Erfolgs-/Misserfolgsmetadaten ohne Nachrichten
für Wiederholungsversuche und Handhabung toter Geräte. Der private VAPID-Schlüssel ist verschlüsselt
`app_settings`; Nur der öffentliche Schlüssel wird an authentifizierte Browser zurückgegeben.

`user_experience` speichert den ersten abgeschlossenen Einführungszeitstempel und den
letzte von jedem Benutzer bestätigte Release-Version. Es enthält keinen Browser
Identifikator oder Geheimnis. Die API leitet ab, ob es sich um Onboarding oder Release Notes handelt
aus diesem Datensatz und der laufenden Anwendungsversion.

`household_budget_settings` speichert ein optionales positives Monatslimit in
Ganzzahlige Cent, die feste EUR-Währung, Warnprozentsatz, letzte Aktualisierung durch den Benutzer
und Zeitstempel für den Haushalt. Durch das Entfernen eines Ziels wird nur diese Einstellung gelöscht.
Budgetzusammenfassungen werden zum Zeitpunkt des Lesens aus den Gesamtsummen der Belege abgeleitet, deren
Die Quittung enthält mindestens eine explizit importierte Zeile. Ausstehende Belege, Gesamtbeträge bei
oder unter Null und andere Währungen bleiben außerhalb der Summe und werden als zurückgegeben
Abdeckungsdiagnose. Es werden keine abgeleiteten monatlichen Hauptbuch- oder Bankdaten gespeichert.

`auth_attempts` speichert nur HMAC-Fingerabdruck-Anmeldequellen und Zeitstempel für
Drosselung. `audit_events` speichert Kategorie, Aktion, Ergebnis und ist datenschutzsicher
Quellfingerabdruck, nicht geheime JSON-Details und Erstellungszeit. Der Besitzer
Operations-API-Projekte nur Kategorie, Routenvorlage, Aktion, Ergebnis, Zeit und
Lokale Akteurbezeichnung aufgelöst; Es werden niemals der Fingerabdruck oder die JSON-Details zurückgegeben.

Für den Zugang mehrerer Haushalte sind nach wie vor explizite Mieterkennungen für jeden erforderlich
Domänentabelle, bevor sie sicher aktiviert werden kann; 0,8,16 bleibt ein Haushalt pro
Installation. Durch die vollständige Löschung werden alle Domänen, Identitäten, Benachrichtigungen usw. gelöscht.
Prüfungs- und Einstellungstabelle, entfernt nur die enthaltenen Quittungsquell- und Produktbilddateien und dann
Initialisiert das leere Schema neu.

Das verbleibende Identitätsschema fügt native Geräteautorisierungen hinzu. Jeder Katalog,
Der Beleg-, Lager-, Einkaufs- und Einstellungsdatensatz erhält eine unveränderliche Gültigkeit
`household_id`, bevor der Zugriff für mehrere Haushalte aktiviert wird. Siehe
[Identität und Authentifizierung](IDENTITY-SECURITY.md).

## Invarianten

- Externe Metadaten können bestätigte Haushaltsdaten nicht stillschweigend ersetzen;
- Fuzzy-Matches können ohne Bestätigung nicht zum Bestand werden;
- Die automatische Beleganalyse führt nie zu einer externen Produktkatalogsuche.
- Eine explizite Anfrage zur Kandidatenbewertung sendet möglicherweise nur den normalisierten Zeilentext
  zur konfigurierten Produktdatenquelle und kann kein Produkt zuordnen;
- Ein Barcode gehört zu einer konkreten Variante und der lokale Barcode stimmt genau überein
  Vorrang vor Namen haben;
- Doppelte Namen, doppelter Barcode-Besitz und veraltete Editor-Schreibvorgänge
  transaktional abgelehnt;
- Aktive Produktreferenzen blockieren das Stammdatenarchiv, während Wareneingang, Lagerbestand oder
  Scan-Referenzen, Blockvariantenlöschung;
- Lokaler Bestand gelingt unabhängig von einem optionalen Anschluss;
- Das Lesen von Grocy-Beständen erfolgt nur in der Vorschau, es werden nur zuvor verknüpfte Produkte abgebildet und
  Der lokale Bestand kann vor der Zählbestätigung nicht mutiert werden.
- Ausgelassene Zählprodukte bleiben unverändert und eine wiederholte Client-Mutation
  Der Bezeichner kann einen Unterschied nicht zweimal anwenden.
- Die Vorschau auf niedrige Lagerbestände ist schreibgeschützt, die Generierung überprüft jedes ausgewählte Produkt erneut.
  und eine Client-Mutationskennung kann Listeneinträge nicht duplizieren;
- Entstandene Engpässe können eine bestehende offene Anfrage erhöhen, jedoch niemals senken;
- Budgeteinstellungen ändern niemals den Beleg- oder Bestandsverlauf und nur explizit
  Für zugesagte Belegsummen kann eine Budgetsumme eingegeben werden.
- destruktive Umschreibungen des Verlaufs werden vermieden;
- Migrationen sind additiv und idempotent.

Der Scanner verwendet unaufgelöste Scan-Entwürfe und idempotente Client-Mutationen
Identifikatoren zusammen mit vorhandenem Barcode, externer Referenz, Lagerbewegung
und Einkaufslistentische. Siehe [Produktscannen](BARCODE-SCANNING.md).
