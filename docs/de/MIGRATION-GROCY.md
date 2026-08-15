# Migration von Grocy

Vorrio kann mit Grocy koexistieren, während ein Haushalt die Arbeitsabläufe ändert.

## Sichere Reihenfolge

1. Sichern Sie beide Anwendungen.
2. Konfigurieren Sie die Grocy-URL und den API-Schlüssel für normale Benutzer in Vorrio.
3. Lassen Sie den Connector während des Übergangs aktiviert.
4. Wählen Sie „Katalog übernehmen“ in den Vorrio-Einstellungen.
5. Überprüfen Sie die Produkt-, Standort-, Einheiten- und Gruppenanzahl.
6. Öffnen Sie **Vorrat → Zählen**, laden Sie den optionalen **Grocy-Vorschlag** und überprüfen Sie ihn
   jeder zugeordnete vorherige/vorgeschlagene Saldo. Physischen Bestand zählen oder korrigieren
   vor der Bestätigung.
7. Lösen Sie nicht zugeordnete Grocy-Produkte durch Katalogimport oder gezielte Lokalisierung auf
   Produkterstellung; Sie werden niemals durch die Bestandsvorschau erstellt.
8. Verwenden Sie Vorrio für die Aufnahme neuer Belege.
9. Deaktivieren Sie den Connector, nachdem Grocy-Export und -Vorschau nicht mehr benötigt werden.

Der Katalogimport ist additiv und idempotent. Grocy-Kennungen werden als gespeichert
externe Referenzen; Wiederholte Importe aktualisieren Metadaten, ohne sie zu duplizieren
Produkt.

## Lagerbestände

Der Katalogimport importiert weiterhin Metadaten, keine Mengen. Version 0.8.2 fügt eine hinzu
separate schreibgeschützte Bestandsvorschau, da historische Belege nicht rekonstruiert werden können
Verbrauch, manuelle Korrekturen oder abgelaufene Lagerbestände zuverlässig.

Die Vorschau aggregiert Grocy-Chargenzeilen und bildet nur Produkte mit einem Import ab
Grocy-Identifikator und listet positive, nicht übereinstimmende Einträge separat auf. Es schreibt
nichts. Nachdem eine Person den Entwurf überprüft und bestätigt hat, nimmt Vorrio einen Einheimischen auf
Zählen Sie Sitzung und Bewegungen. Grocy bleibt unverändert und wird nicht als behandelt
bidirektionale Synchronisationsquelle.

## Rollback

Durch das Deaktivieren des Connectors werden keine Grocy-Daten geändert. Wenn ein Vorrio-Release sein muss
Zurücksetzen, Wiederherstellen des Vorrio-Volumes vor dem Upgrade mit dem passenden Image und
geheimer Schlüssel. Führen Sie keine ältere Binärdatei für eine migrierte Nur-Kopie-Datenbank aus.
