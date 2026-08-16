# Sichern und Wiederherstellen

## Was gesichert werden soll

Das persistente `/data`-Volume enthält:

- `app.db` und SQLite WAL-Dateien;
- verschlüsselte Anwendungseinstellungen;
- Erhalten Sie Belegbilder und PDFs unter `receipts/`.
- Lokal hochgeladene Produktbilder unter `product-images/`.

`APP_SECRET_KEY` befindet sich nicht im Volume. Sichern Sie es separat in einem Passwort
Manager oder Geheimnissystem. Ohne den gleichen Schlüssel, hinterlegten Provider und Connector
Anmeldeinformationen können nicht entschlüsselt werden.

## Konsistente Sicherung

Stoppen Sie den Container kurz oder verwenden Sie den Online-Backup-Befehl von SQLite von einem vertrauenswürdigen Server
Wartungscontainer. Das Kopieren nur von `app.db`, während Schreibvorgänge aktiv sind, kann entfallen
WAL-Daten.

Empfohlenes einfaches Verfahren:

1. Stoppen Sie den Vorrio-Behälter;
2. den kompletten Datenbestand archivieren;
3. Starten Sie den Container;
4. Überprüfen Sie das Archiv und notieren Sie die Anwendungsversion.
5. Speichern Sie `APP_SECRET_KEY` separat.

## Wiederherstellen

1. Stoppen Sie den Behälter;
2. Wiederherstellung des gesamten Inhalts und Eigentums des Volumes;
3. Stellen Sie das passende `APP_SECRET_KEY` wieder her;
4. Starten Sie dasselbe oder ein neueres kompatibles Image.
5. Überprüfen Sie die Anmeldung, die Kataloganzahl, die letzten Belege und `/api/health`.

Führen Sie niemals zwei SQLite-Kopien durch Dateiersetzung zusammen. Der Besitzer-ZIP-Export hinzugefügt
in 0.8.15 bietet lesbare Portabilität, ist aber absichtlich keine Datenbank
Wiederherstellungsformat und schließt alle Authentifizierungs-/Anbieter-/Connector-Geheimnisse aus.

## `APP_SECRET_KEY` drehen

Wenn Sie den Wert ändern, ohne die verschlüsselten Einstellungen zu migrieren, wird der Anbieter gespeichert
und Connector-Anmeldeinformationen sind nicht lesbar. Verwenden Sie das mitgelieferte Offline-Rotationstool:

1. Erstellen Sie ein vollständiges Volume-Backup und stoppen Sie Vorrio.
2. Generieren Sie ein neues Geheimnis und bewahren Sie beide Werte in einer geschützten temporären Umgebung auf
   Datei- oder Geheimnismanager;
3. Führen Sie dasselbe Vorrio-Image als einmaligen Wartungscontainer mit den Daten aus
   volume, der alte Wert als `APP_SECRET_KEY` und der neue Wert als
   `APP_SECRET_KEY_NEW`:

```bash
docker run --rm \
  --volume vorrio_data:/data \
  --env APP_SECRET_KEY \
  --env APP_SECRET_KEY_NEW \
  --entrypoint python \
  vorrio:0.8.27 /app/scripts/rotate_secret.py
```

4. Aktualisieren Sie `APP_SECRET_KEY` der normalen Bereitstellung auf den neuen Wert.
5. Starten Sie Vorrio und überprüfen Sie Anmeldung, Einstellungen und Anschlüsse;
6. Entfernen Sie das alte Geheimnis erst, nachdem die Überprüfung erfolgreich war.

Das Tool überprüft die Entschlüsselung mit dem alten Schlüssel, bevor etwas geändert oder erstellt wird
`app.db.backup_before_secret_rotation_<timestamp>` in `/data`, verschlüsselt die neu
Einstellungen, markiert jede serverseitige Browsersitzung als widerrufen und schreibt ein Audit
Ereignis. Durch das Ändern des Signaturschlüssels wird auch jedes signierte Cookie konstruktionsbedingt ungültig.
Wenn die Überprüfung fehlschlägt, beenden Sie den Vorgang und stellen Sie ihn wieder her
die vollständige Sicherung; Löschen Sie niemals den einzigen funktionierenden alten Schlüssel.

## Release-Überprüfung

Für 0.8.23 testen die Betreuer ein neues leeres Volume, ein Erstinstallationssetup und eine Familie
Einladungs- und Rollenstatus, Passkey/TOTP/Wiederherstellungsschema, Status der letzten Authentifizierung,
Erstellungs-/Umfangs-/Widerrufsstatus des API-Tokens, vollständiges Archiv des gestoppten Volumes,
Wiederherstellung auf einem zweiten leeren Volume, SQLite
`PRAGMA integrity_check`, Eigentümer-/Sitzungsstatus und Anmeldung wiederhergestellt. Das Verfahren verwendet
synthetische Daten und das gleiche Produktionsbild. Die automatisierte Startreise auch
umfasst die Katalog-/Barcode-Erstellung, den überprüften Belegeingang, den Lagerbestand, das Budget,
tragbarer Export und die Betriebsprojektion. Destruktive Löschtests verwenden a
separates temporäres Volume. Betreiber sollten dennoch ihr eigenes Backup testen
Ziel- und Aufbewahrungsrichtlinie.
