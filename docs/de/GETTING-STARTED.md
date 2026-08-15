# Erste Schritte in Vorrio

Vorrio hat eine Hauptgeschichte:

```text
purchase -> review -> local product knowledge -> stock -> shopping
```

Nichts ändert den Lagerbestand, nur weil ein KI-Modell oder eine Produktdatenbank einen gefunden hat
mögliche Übereinstimmung. Vorrio präsentiert zunächst das Ergebnis und seine Beweise; ein Haushalt
Das Mitglied bestätigt das beabsichtigte Produkt und die beabsichtigte Aktion.

## Sprache

Der abgemeldete Bildschirm folgt zunächst dem Browser und unterstützt Deutsch und
Englisch. Beim ersten Setup und bei der Einladungsannahme wird diese Sprache für gespeichert
neues Konto. Nach der Anmeldung ist die gespeicherte Auswahl jedes Benutzers maßgeblich
Geräte und können unter **Einstellungen → Sprache & Region** geändert werden.

Die gleiche Installation enthält alle offiziellen Sprachen. Vorrio lädt die
den ausgewählten Katalog von seinem eigenen Server und speichert ihn für spätere Offline-Starts zwischen. Zu
Wechseln Sie zu einer Sprache, die auf diesem Gerät noch nie verwendet wurde, und stellen Sie die Verbindung einmal her
Das entsprechende Paket kann lokal gespeichert werden.

Bei einer Änderung der Benutzeroberfläche werden bekannte Produktnamen niemals übersetzt oder neu geschrieben.
Marken, Geschäftsnamen, Quittungstext, Währung oder die Zeitzone des Servers. Siehe
[Lokalisierung](LOCALIZATION.md) für das genaue Verhalten.

## Erster Login

Nachdem ein Eigentümer die Installation erstellt hat und nach jedem eingeladenen Konto zuerst
Login, Vorrio öffnet eine dreistufige Einführung:

1. **Der Hauptablauf** erklärt, wie ein Beleg zum überprüften Bestand wird.
2. **Die beiden Eingabepfade** unterscheiden einen gesamten Kauf von einem Paketscan.
3. **Die Sicherheitsgrenze** erklärt, dass Vorschläge Vorschläge bleiben, bis a
   Person bestätigt sie.

Der letzte Schritt erfolgt direkt mit der Erfassung von Quittungen oder dem Scannen von Paketen. Ein Zuschauer
wird stattdessen in den schreibgeschützten Bestandsarbeitsbereich verschoben. **Später** schließt den Guide
ohne es fälschlicherweise als vollständig zu markieren; Beim nächsten Login erscheint es wieder, bis a
Die endgültige Startaktion wird ausgewählt. Es kann jederzeit wieder geöffnet werden
**Einstellungen → Hilfe & Version**.

## Wo man Dinge findet

| Bereich | Verwenden Sie es für |
|---|---|
| **Start** | Fotografieren Sie einen vollständigen Beleg, laden Sie ein Bild/PDF hoch und öffnen Sie aktuelle Belege erneut. |
| **Scannen** | Identifizieren Sie einen Barcode, fügen Sie Lagerbestände hinzu oder verbrauchen Sie sie, markieren Sie ein Paket als geöffnet oder fügen Sie es der Einkaufsliste hinzu. |
| **Vorrat** | Finden und bearbeiten Sie Produkte, Varianten, Barcodes, Bilder, Standorte und aktuelle Mengen. |
| **Einkäufe** | Nutzen Sie die Einkaufsliste, Vorschläge für geringe Lagerbestände, den Preisverlauf, das Budget und den Belegverlauf. |
| **Einstellungen** | Verwalten Sie Konto, Familie, Sicherheit, Benachrichtigungen, optionale Connectors, Datenschutz, Betrieb und Hilfe. |

## Nach einem Update

Der Betreiber kontrolliert weiterhin Docker-Updates. Vorrio zieht nicht und startet es nicht neu
eigener Container. Wenn ein neues Image bewusst bereitgestellt und angewendet wird
Bei Versionsänderungen sieht jedes Konto die Kurzversion der installierten Version
Notizen einmal nach dem Login. Die Bestätigung wird pro Benutzer auf dem Server gespeichert
Datenbank, so dass ein Wechsel des Browsers oder die Installation der PWA nicht zu einer Wiederholung führt.

Das Schließen mit **Später lesen** stellt keine Anerkennung der Veröffentlichung dar; es kann erscheinen
erneut nach einem späteren Login. **Verstanden** zeichnet die laufende Version auf. Aktuell
Hinweise bleiben unter **Einstellungen → Hilfe & Version → Was ist neu?** verfügbar.

Vorrio meldet, was bereits installiert ist. Es kontaktiert weder GitHub noch a
Registrierung, um ein verfügbares Update anzukündigen, und dies bedeutet nicht, dass `latest`
wurde erfolgreich gezogen. Betreiber sollten weiterhin das dokumentierte Backup verwenden,
Pull-, Neuerstellungs- und Zustands-/Bereitschaftsprüfungen in [Installation](INSTALLATION.md).

## Konto- und Datenverhalten

- Der Abschluss der Einführung und die bestätigte Version gehören dem Benutzer, nicht dem
  Browser.
- Der Staat enthält kein Passwort, Token oder Haushaltsinhalte.
- Der tragbare Export berücksichtigt persönliche Präferenzen.
- Vollständiges Löschen der Installation löscht es.
- Automatisierungstoken können es nicht lesen oder ändern.
