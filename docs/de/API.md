# REST-API

Vorrio stellt eine versionierte JSON-API unter `/api/v1` bereit. Die PWA nutzt dasselbe
Vertrag als externe Integrationen. Die Browserauthentifizierung verwendet eine signierte
HttpOnly-Cookie mit einem zufälligen Token, das durch eine widerrufbare Serversitzung unterstützt wird.

- Swagger-Benutzeroberfläche: `/docs`
- ReDoc: `/redoc`
- OpenAPI 3.1-Vertrag: `/openapi.json`
- Gesundheitscheck: `/api/health`
- Bereitstellungsbereitschaft: `/api/readiness`

Der generierte Vertrag wird unter `docs/api/openapi.json` gespeichert. Lauf
`make api-docs` nach jeder API-Änderung und `make api-docs-check` davor
eine Änderung einreichen.

## Endpunkte

| Methode | Pfad | Gruppe | Zusammenfassung | Veraltet |
|---|---|---|---|---|
| `GET` | `/api/health` | System | Instanzzustand prüfen | nein |
| `GET` | `/api/readiness` | System | Bereitstellungsbereitschaft prüfen | nein |
| `GET` | `/api/v1/auth/api-token-scopes` | Authentifizierung | Verfügbare Bereiche für Automatisierungstoken auflisten | nein |
| `GET` | `/api/v1/auth/api-tokens` | Authentifizierung | Listen Sie die Automatisierungstoken des aktuellen Kontos auf | nein |
| `POST` | `/api/v1/auth/api-tokens` | Authentifizierung | Erstellen Sie ein Automatisierungstoken mit Gültigkeitsbereich | nein |
| `DELETE` | `/api/v1/auth/api-tokens/{token_id}` | Authentifizierung | Ein Automatisierungstoken widerrufen | nein |
| `GET` | `/api/v1/auth/invitations` | Authentifizierung | Aktive Haushaltseinladungen auflisten | nein |
| `POST` | `/api/v1/auth/invitations` | Authentifizierung | Erstellen Sie eine Einweg-Haushaltseinladung | nein |
| `DELETE` | `/api/v1/auth/invitations/{invitation_id}` | Authentifizierung | Eine ungenutzte Haushaltseinladung widerrufen | nein |
| `GET` | `/api/v1/auth/invitations/{token}` | Authentifizierung | Lesen Sie eine Einladung zur einmaligen Verwendung | nein |
| `POST` | `/api/v1/auth/invitations/{token}/accept` | Authentifizierung | Nehmen Sie eine Einladung an und erstellen Sie das Mitgliedskonto | nein |
| `POST` | `/api/v1/auth/login` | Authentifizierung | Erstellen Sie eine Haushaltssitzung | nein |
| `POST` | `/api/v1/auth/logout` | Authentifizierung | Aktuelle Sitzung beenden | nein |
| `GET` | `/api/v1/auth/me` | Authentifizierung | Aktuelle Sitzung validieren | nein |
| `GET` | `/api/v1/auth/members` | Authentifizierung | Haushaltsmitglieder auflisten | nein |
| `PATCH` | `/api/v1/auth/members/{user_id}` | Authentifizierung | Eine Mitgliedsrolle oder einen Zugriffsstatus ändern | nein |
| `POST` | `/api/v1/auth/mfa/verify` | Authentifizierung | Beenden Sie eine Passwort-Anmeldung mit einem zweiten Faktor | nein |
| `POST` | `/api/v1/auth/passkeys/authentication/begin` | Authentifizierung | Passwortlose Passkey-Authentifizierung starten | nein |
| `POST` | `/api/v1/auth/passkeys/authentication/complete` | Authentifizierung | Vollständige passwortlose Passkey-Authentifizierung | nein |
| `POST` | `/api/v1/auth/passkeys/registration/begin` | Authentifizierung | Passkey-Registrierung starten | nein |
| `POST` | `/api/v1/auth/passkeys/registration/complete` | Authentifizierung | Überprüfen und speichern Sie einen Passkey | nein |
| `DELETE` | `/api/v1/auth/passkeys/{credential_id}` | Authentifizierung | Einen Passkey löschen | nein |
| `PUT` | `/api/v1/auth/password` | Authentifizierung | Ändern Sie das aktuelle Kontopasswort | nein |
| `PATCH` | `/api/v1/auth/preferences` | Authentifizierung | Persönliche Benutzeroberflächeneinstellungen aktualisieren | nein |
| `PATCH` | `/api/v1/auth/profile` | Authentifizierung | Vervollständigen oder aktualisieren Sie das Eigentümerprofil | nein |
| `POST` | `/api/v1/auth/reauthenticate` | Authentifizierung | Bestätigen Sie die Identität vor einer sensiblen Änderung | nein |
| `POST` | `/api/v1/auth/recovery` | Authentifizierung | Wiederherstellen eines Kontos mit einem Wiederherstellungscode zur einmaligen Verwendung | nein |
| `POST` | `/api/v1/auth/recovery-codes` | Authentifizierung | Ersetzen Sie alle Einmal-Wiederherstellungscodes | nein |
| `GET` | `/api/v1/auth/security` | Authentifizierung | Passkey, TOTP und Wiederherstellungsstatus lesen | nein |
| `GET` | `/api/v1/auth/sessions` | Authentifizierung | Aktive Browsersitzungen auflisten | nein |
| `POST` | `/api/v1/auth/sessions/revoke-others` | Authentifizierung | Jede zweite Browsersitzung widerrufen | nein |
| `DELETE` | `/api/v1/auth/sessions/{session_id}` | Authentifizierung | Eine Browsersitzung widerrufen | nein |
| `POST` | `/api/v1/auth/setup` | Authentifizierung | Komplette Ersteinrichtung | nein |
| `GET` | `/api/v1/auth/state` | Authentifizierung | Setup und Sitzungsstatus lesen | nein |
| `DELETE` | `/api/v1/auth/totp` | Authentifizierung | Authentifizierungs-App-Überprüfung deaktivieren | nein |
| `POST` | `/api/v1/auth/totp/enable` | Authentifizierung | Überprüfen und aktivieren Sie eine Authentifizierungs-App | nein |
| `POST` | `/api/v1/auth/totp/setup` | Authentifizierung | Erstellen Sie ein ausstehendes Authentifikator-App-Geheimnis | nein |
| `GET` | `/api/v1/catalog/barcodes/{barcode}/lookup` | Katalog | Lösen Sie einen Barcode lokal oder über Open Facts | auf nein |
| `GET` | `/api/v1/catalog/master-data` | Katalog | Standorte, Einheiten und Produktgruppen auflisten | nein |
| `POST` | `/api/v1/catalog/master-data/{kind}` | Katalog | Erstellen Sie einen Katalogstammdateneintrag | nein |
| `PATCH` | `/api/v1/catalog/master-data/{kind}/{item_id}` | Katalog | Einen Katalogstammdateneintrag umbenennen oder bearbeiten | nein |
| `DELETE` | `/api/v1/catalog/master-data/{kind}/{item_id}` | Katalog | Archivieren Sie einen nicht verwendeten Katalogstammdateneintrag | nein |
| `GET` | `/api/v1/catalog/products` | Katalog | Katalogprodukte durchsuchen | nein |
| `POST` | `/api/v1/catalog/products` | Katalog | Erstellen Sie ein lokales Katalogprodukt | nein |
| `GET` | `/api/v1/catalog/products/{product_id}` | Katalog | Ein Produkt mit Varianten und Barcodes lesen | nein |
| `PATCH` | `/api/v1/catalog/products/{product_id}` | Katalog | Bearbeiten Sie ein lokales Katalogprodukt | nein |
| `GET` | `/api/v1/catalog/products/{product_id}/image` | Katalog | Lesen Sie ein lokal verwaltetes Produktbild | nein |
| `POST` | `/api/v1/catalog/products/{product_id}/image` | Katalog | Laden Sie ein privates Produktbild hoch | nein |
| `DELETE` | `/api/v1/catalog/products/{product_id}/image` | Katalog | Aktuelles Produktbild entfernen | nein |
| `GET` | `/api/v1/catalog/products/{product_id}/price-history` | Katalog | Quittungspreise für ein Katalogprodukt auflisten | nein |
| `POST` | `/api/v1/catalog/products/{product_id}/variants` | Katalog | Eine verkaufbare Produktvariante hinzufügen | nein |
| `POST` | `/api/v1/catalog/reconcile` | Katalog | Nicht aufgelöste Wareneingangszeilen neu bewerten | nein |
| `PATCH` | `/api/v1/catalog/variants/{variant_id}` | Katalog | Bearbeiten Sie eine Produktvariante | nein |
| `DELETE` | `/api/v1/catalog/variants/{variant_id}` | Katalog | Eine nicht verwendete Produktvariante löschen | nein |
| `POST` | `/api/v1/catalog/variants/{variant_id}/barcodes` | Katalog | Fügen Sie einer Produktvariante einen Barcode hinzu | nein |
| `DELETE` | `/api/v1/catalog/variants/{variant_id}/barcodes/{barcode}` | Katalog | Trennen Sie einen Barcode von einer Produktvariante | nein |
| `GET` | `/api/v1/experience` | Erfahrung | Lesen Sie den Status des persönlichen Onboardings und der Versionshinweise | nein |
| `PUT` | `/api/v1/experience` | Erfahrung | Schließen Sie das Onboarding ab oder bestätigen Sie die aktuelle Version | nein |
| `GET` | `/api/v1/grocy/master-data` | Legacy Grocy | Grocy-Stammdaten lesen | ja |
| `GET` | `/api/v1/grocy/products` | Legacy Grocy | Suche nach Grocy-Produkten | ja |
| `GET` | `/api/v1/insights/budget` | Einblicke | Fassen Sie das Haushaltsbudget anhand bestätigter Belege zusammen | nein |
| `PUT` | `/api/v1/insights/budget/settings` | Einblicke | Gemeinsames monatliches Haushaltsbudget festlegen oder löschen | nein |
| `GET` | `/api/v1/insights/prices` | Einblicke | Bestätigte Wareneingangspreise nach Produkt und Filiale zusammenfassen | nein |
| `POST` | `/api/v1/integrations/grocy/import-catalog` | Integrationen | Importieren oder aktualisieren Sie den lokalen Katalog aus Grocy | nein |
| `GET` | `/api/v1/integrations/grocy/stock-preview` | Integrationen | Vorschau der zugeordneten Grocy-Guthaben, ohne Vorrio zu ändern | nein |
| `PUT` | `/api/v1/notifications/preferences` | Benachrichtigungen | Persönliche Aktienbenachrichtigungseinstellungen aktualisieren | nein |
| `GET` | `/api/v1/notifications/state` | Benachrichtigungen | Persönliche Web Push-Einstellungen und Geräte lesen | nein |
| `POST` | `/api/v1/notifications/subscriptions` | Benachrichtigungen | Registrieren oder aktualisieren Sie ein Browser-Push-Gerät | nein |
| `DELETE` | `/api/v1/notifications/subscriptions/{subscription_id}` | Benachrichtigungen | Ein persönliches Push-Gerät widerrufen | nein |
| `POST` | `/api/v1/notifications/test` | Benachrichtigungen | Senden Sie eine sichtbare Testbenachrichtigung an ein persönliches Gerät | nein |
| `GET` | `/api/v1/operations/overview` | Datenschutz und Betrieb | Lesen Sie die Übersicht über datenschutzsichere Eigentümervorgänge | nein |
| `GET` | `/api/v1/privacy/export` | Datenschutz und Betrieb | Laden Sie einen geheimnisfreien tragbaren Haushaltsexport herunter | nein |
| `GET` | `/api/v1/privacy/export/preview` | Datenschutz und Betrieb | Vorschau des tragbaren Haushaltsexports | nein |
| `DELETE` | `/api/v1/privacy/household` | Datenschutz und Betrieb | Diese Einfamilienhausinstallation dauerhaft löschen | nein |
| `GET` | `/api/v1/privacy/retention` | Datenschutz und Betrieb | Vorschau der Aufbewahrung von Belegdateien | nein |
| `POST` | `/api/v1/privacy/retention/run` | Datenschutz und Betrieb | Jetzt Quittungsdateiaufbewahrung anwenden | nein |
| `GET` | `/api/v1/receipts` | Quittungen | Aktuelle Belege auflisten | nein |
| `POST` | `/api/v1/receipts/analyze` | Quittungen | Analysieren Sie eine Bild- oder PDF-Quittung | nein |
| `GET` | `/api/v1/receipts/{receipt_id}` | Quittungen | Holen Sie sich eine Quittung mit allen Zeilen | nein |
| `POST` | `/api/v1/receipts/{receipt_id}/import` | Quittungen | Überprüfte Zeilen in den lokalen Bestand übernehmen | nein |
| `PATCH` | `/api/v1/receipts/{receipt_id}/items/{item_id}` | Quittungen | Eine Belegposition einem Katalogprodukt zuordnen | nein |
| `POST` | `/api/v1/receipts/{receipt_id}/items/{item_id}/candidate` | Quittungen | Bestätigen und lernen Sie einen echten Produktkandidaten | nein |
| `GET` | `/api/v1/receipts/{receipt_id}/items/{item_id}/candidates` | Quittungen | Finden Sie echte Produktkandidaten für eine Empfangszeile | nein |
| `POST` | `/api/v1/receipts/{receipt_id}/items/{item_id}/catalog-product` | Quittungen | Erstellen und Zuordnen eines lokalen Katalogprodukts | nein |
| `POST` | `/api/v1/receipts/{receipt_id}/items/{item_id}/create-product` | Legacy Grocy | Erstellen und zuordnen Sie ein Grocy-Produkt | ja |
| `POST` | `/api/v1/scans/resolve` | Scannen | Einen Paketcode auflösen, ohne den Lagerbestand zu ändern | nein |
| `GET` | `/api/v1/scans/unresolved` | Scannen | Nicht aufgelöste Paketscans auflisten | nein |
| `GET` | `/api/v1/scans/{scan_id}` | Scannen | Einen Scan-Entwurf lesen | nein |
| `PATCH` | `/api/v1/scans/{scan_id}` | Scannen | Einen ungelösten Scan bearbeiten oder zuordnen | nein |
| `DELETE` | `/api/v1/scans/{scan_id}` | Scannen | Einen nicht aufgelösten Scan verwerfen | nein |
| `POST` | `/api/v1/scans/{scan_id}/confirm` | Scannen | Bestätigen Sie die ausgewählte Paketaktion | nein |
| `GET` | `/api/v1/settings` | Einstellungen | Öffentliche Einstellungen lesen | nein |
| `PUT` | `/api/v1/settings` | Einstellungen | Instanzeinstellungen ersetzen | nein |
| `POST` | `/api/v1/settings/test-grocy` | Einstellungen | Testen Sie den Grocy-Anschluss | nein |
| `POST` | `/api/v1/settings/test-provider` | Einstellungen | Testen Sie den ausgewählten Analyseanbieter | nein |
| `GET` | `/api/v1/shopping-list` | Einkaufen | Offene Haushaltseinkäufe auflisten | nein |
| `POST` | `/api/v1/shopping-list/generate` | Einkaufen | Generieren Sie überprüfte Einkaufslistenartikel aus geringen Lagerbeständen | nein |
| `GET` | `/api/v1/shopping-list/low-stock` | Einkaufen | Vorschau der Produkte unterhalb des konfigurierten Mindestbestands | nein |
| `PATCH` | `/api/v1/shopping-list/{item_id}` | Einkaufen | Bearbeiten oder vervollständigen Sie einen Einkaufslisteneintrag | nein |
| `GET` | `/api/v1/status` | System | Instanz- und Connectorstatus lesen | nein |
| `GET` | `/api/v1/stock/count/products` | Lager | Produkte für eine überprüfte Bestandszählung auflisten | nein |
| `GET` | `/api/v1/stock/counts` | Lager | Abgeschlossene Bestandszählungen auflisten | nein |
| `POST` | `/api/v1/stock/counts` | Lager | Anwenden einer überprüften Öffnungs- oder Korrekturzählung | nein |

## Kompatibilität

Pfade vor Version 0.6 unter `/api` werden vom Server vorübergehend akzeptiert, sind es aber
nicht Teil des kanonischen Vertrags. Neue Kunden müssen `/api/v1` verwenden.
