# Datenschutz, Portabilität und Löschung

Bei Vorrio steht der Ort an erster Stelle, aber lokale Daten benötigen dennoch einen verständlichen Lebenszyklus.
Version 0.8.15 stellt dem Hausbesitzer einen Platz unter **Einstellungen** zur Verfügung
Überprüfen Sie den Speicher, laden Sie eine tragbare Kopie herunter und wenden Sie die Aufbewahrungsfrist für Quittungsdateien an
Regel und löschen Sie die Einfamilienhausinstallation.

## Tragbarer Export

`GET /api/v1/privacy/export/preview` meldet die Datensätze und aufbewahrten Quelldateien
und lokal verwaltete Produktbilder, die exportiert werden können. `GET /api/v1/privacy/export` gibt nach a eine ZIP zurück
aktuelle Besitzerauthentifizierung. Der Anrufer kann Belegbilder/PDFs dabei ausschließen
Beibehaltung aller erkannten Belegdaten. Lokal hochgeladene Produktbilder sind immer vorhanden
unter `product-images/` enthalten, sodass der Katalog portierbar bleibt.

Die ZIP-Datei enthält eine versionierte `manifest.json`, SHA-256-Prüfsumme und ist lesbar
JSON-Abschnitte für Haushalts-/Mitgliedsmetadaten, öffentliche Präferenzen, Katalog,
Quittungen, Lagerbestände, Einkäufe, Scans und eine bereinigte Prüfhistorie. Es absichtlich
Ausgenommen sind Passwort-Hashes, rohe oder gehashte Sitzungs-/Einladungs-/API-Tokens, TOTP und
Wiederherstellungsmaterial, Hauptschlüssel/Herausforderungen, Anbieter-/Connector-Schlüssel, Web Push
Endpunkte/Schlüssel und Fingerabdrücke von Netzwerkquellen.

Zu den persönlichen Vorlieben gehört die gewählte Oberflächensprache, ob die
Die Einführung wurde abgeschlossen und die letzte anerkannte Vorrio-Version. Sie
enthalten kein Geheimnis und werden exportiert, damit ein Haushalt verstehen kann, warum a
Sprache, Anleitung oder Versionshinweis werden angezeigt. Beim vollständigen Löschen werden diese Datensätze gelöscht
mit dem Konto.

Hierbei handelt es sich um einen tragbaren Export von Haushaltsdaten, nicht um ein Backup zur Notfallwiederherstellung. A
Für eine funktionierende Wiederherstellung sind weiterhin das vollständige `/data`-Volume und das entsprechende erforderlich
`APP_SECRET_KEY`; siehe [Sichern und Wiederherstellen](BACKUP-RESTORE.md).

## Aufbewahrung der Belegdatei

Die Datenschutzeinstellung gilt nur für Belegquellbilder und PDFs. Produkt
Bilder bleiben im Katalog, bis sie ersetzt, entfernt oder der Haushalt gelöscht wird. Anerkannte Linien,
Bestätigte Zuordnungen, Preise, Zugänge und Lagerbewegungen bleiben weiterhin verfügbar.

- **Nach Analyze löschen** entfernt die Quelle sofort nach Erfolg
  Analyse und macht ältere aufbewahrte Dateien bei der nächsten Bereinigung verfügbar.
- **Aufbewahrung in Tagen** behält Quellen bis zum konfigurierten Cutoff. `0`
  bedeutet sofort förderfähig.
- Vorrio wertet die Regel im einzelnen Anwendungscontainer nach dem Start aus
  und dann stündlich. Der Eigentümer kann es sofort in der Vorschau anzeigen und ausführen.
– Ein Datenbankpfad, der außerhalb von `/data/receipts` aufgelöst wird, wird abgelehnt und niemals
  gelöscht. Der abgelehnte Zeiger bleibt für eine Reparatur durch den Bediener sichtbar.

## Operative Sicht und Audit-Minimierung

Die Besitzeransicht meldet SQLite `quick_check`, Datenbankgröße, aktive Sitzung und
Geräteanzahl, ausstehende Arbeiten, Ausfälle in den letzten 24 Stunden und aktuelle Ereignisse.
Es werden keine Roh-IP-Adressen, Quell-Fingerabdrücke, Audit-Detail-JSON usw. zurückgegeben.
Anforderungsabfragezeichenfolgen oder in URLs eingebettete Ressourcenkennungen. Verwendung von HTTP-Protokollen
nur die API-Routenvorlage, den Status, die Dauer und eine zufällige Anforderungs-ID; Standard
Die Uvicorn-Client-Adresszugriffsprotokollierung ist deaktiviert.

## Dauerhafte Löschung

`DELETE /api/v1/privacy/household` ist nur für den Besitzer und erfordert eine Authentifizierung von
die letzten zehn Minuten und akzeptiert nur die wörtliche Bestätigung
`HAUSHALT ENDGÜLTIG LÖSCHEN`. Die PWA fügt eine zweite Browserbestätigung hinzu. Es
löscht Konten, Sitzungen, Einstellungen, Katalog, Belege, Lagerbestände, Einkaufsdaten,
Audit-Aufzeichnungen, einbehaltene Quittungsdateien und lokale Produktbilder und sendet dann die Installation an zurück
Erstmaliges Setup.

Die Löschung erfolgt absichtlich installationsweit, da Vorrio dies derzeit unterstützt
ein Haushalt pro Einsatz. Es kann nicht rückgängig gemacht werden. Laden Sie einen Export herunter und erstellen Sie ihn
Zuerst ein getestetes Volume-Backup. Automatisierte Tests führen die Löschung nur gegen eine neue durch
temporäre Datenbank; Release-Prüfungen rufen es niemals für ein bereitgestelltes Volume auf.

## REST-Endpunkte

| Methode | Pfad | Zweck |
|---|---|---|
| `GET` | `/api/v1/privacy/export/preview` | Vorschau der tragbaren Daten und Dateigröße |
| `GET` | `/api/v1/privacy/export` | Laden Sie geheimnisfreies ZIP | herunter
| `GET` | `/api/v1/privacy/retention` | Vorschau geeigneter Quelldateien |
| `POST` | `/api/v1/privacy/retention/run` | Wenden Sie jetzt die konfigurierte Regel an |
| `GET` | `/api/v1/operations/overview` | Lesen Sie die datenschutzsichere Gesundheits- und Audit-Zusammenfassung |
| `DELETE` | `/api/v1/privacy/household` | Die Installation dauerhaft löschen |

Alle Endpunkte erfordern die Browsersitzung des Besitzers. Export, manuelle Bereinigung und
Löschvorgänge erfordern außerdem eine aktuelle Authentifizierung und sind für die API nicht verfügbar
Token.
