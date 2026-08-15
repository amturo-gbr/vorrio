# Web-Push-Benachrichtigungen

Vorrio kann beim Kauf eines Produkts persönliche, optionale Browser-Benachrichtigungen senden
in den Zustand „Niedriger Lagerbestand“ übergeht oder ein Lagerlos in das konfigurierte Mindesthaltbarkeitsdatum übergeht
Fenster. Es wird keine Benachrichtigungsberechtigung automatisch und keine externe angefordert
Benachrichtigungskonto ist erforderlich.

## Benutzerworkflow

1. Öffnen Sie Vorrio über seine stabile private HTTPS-URL.
2. Fügen Sie Vorrio auf dem iPhone oder iPad zum Startbildschirm hinzu und öffnen Sie die installierte App.
3. Melden Sie sich an und öffnen Sie **Einstellungen → Bestandsbenachrichtigungen**.
4. Wählen Sie **Benachrichtigungen zulassen** und akzeptieren Sie die Aufforderung des Betriebssystems.
5. Wählen Sie Warnungen bei niedrigem Lagerbestand und/oder Ablauf, wählen Sie das Ablauffenster und speichern Sie.
6. Verwenden Sie **Test senden**, um das aktuelle Gerät zu überprüfen.

Jede Browserinstallation ist ein separates Geräteabonnement. Entfernen eines Geräts
widerruft seinen Servereintrag und meldet den aktuellen Browser ab. Das Globale
Der persönliche Schalter kann die Lieferung unterbrechen, während die Geräte registriert bleiben.

## Ereignisverhalten

- Niedriger Lagerbestand ist nur zulässig, wenn `minimum_stock_quantity > 0` und die summierte
  Die aktuellen Lose liegen bei oder unter diesem Minimum.
- Das Verfallsdatum gilt nur für Lose mit Restmenge und Mindesthaltbarkeitsdatum
  Datum innerhalb des 0–90-Tage-Warnfensters des Benutzers.
- Vorrio sendet ein Ereignis, wenn die Bedingung aktiv wird. Wiederholte Kontrollen reichen aus
  nicht wiederholen.
- Die Veranstaltung wird erst dann wieder teilnahmeberechtigt, wenn sich der Bestand erholt hat oder abgelaufen ist
  Zustand verschwindet. Durch das Deaktivieren einer Benachrichtigungsart wird auch deren Offenheit behoben
  Ereignisse, so dass bei bewusster erneuter Aktivierung der aktuelle Zustand erneut ausgewertet wird.
- Eine fehlgeschlagene Zustellung kann weiterhin wiederholt werden. HTTP 404/410-Antworten von einem Push
  Der Dienst widerruft das tote Gerät automatisch.
- Nachrichtentitel, Nachrichtentext, Nummern und Datumsangaben verwenden das gespeicherte Deutsch des empfangenden Benutzers
  oder englische Oberflächensprache. Produkt- und Gerätenamen bleiben Eigentum des Haushalts
  Originaldaten. Das Ändern der Sprache wirkt sich auf spätere Ereignisse und Testnachrichten aus;
  Es wird ein bereits übermittelter Zustandsübergang nicht erneut gesendet.

Der prozessinterne Evaluator wird standardmäßig alle 15 Minuten ausgeführt. Es ist absichtlich so
klein und passend für den betreuten Einzelcontainer/Einzelhaushalt
Bereitstellung. Eine persistente externe Jobwarteschlange bleibt ein späteres Scale-out-Gate.

## Datenschutz und Schlüsselspeicherung

Browser-Abonnement-Endpunkte und ihre `p256dh`/`auth`-Schlüssel werden unter verschlüsselt
Rest mit `APP_SECRET_KEY`. Der private VAPID-Schlüssel wird zunächst lokal generiert
verwenden und mit demselben Schlüssel verschlüsseln; Nur der öffentliche Anwendungsserverschlüssel ist vorhanden
an einen authentifizierten Browser zurückgegeben. Vorrio hält sich an die Lieferfrist von 90 Tagen
Datensätze ohne Nachrichteninhalt, rohe IP-Adressen oder vollständige User-Agent-Strings.

Durch Rotieren von `APP_SECRET_KEY` werden Verbindungseinstellungen, TOTP-Geheimnisse usw. neu verschlüsselt
VAPID-Schlüssel und jedes Push-Abonnement, bevor Browsersitzungen ungültig werden.

## Konfiguration

| Variable | Standard | Zweck |
|---|---|---|
| `WEB_PUSH_SUBJECT` | `mailto:admin@vorrio.local` | VAPID-Kontaktanspruch. Öffentliche Distributionen sollten einen echten `mailto:`- oder HTTPS-Kontakt verwenden. |
| `NOTIFICATION_CHECK_SECONDS` | `900` | Auswertungsintervall, beschränkt auf 60–86400 Sekunden. |

Web Push erfordert einen sicheren Browserkontext. LAN HTTP bleibt verfügbar für
Manuelle Verwendung, aber Kamera-, Passkey- oder Push-Funktionen können nicht registriert werden. iOS und
iPadOS unterstützt standardbasiertes Web Push für Home-Screen-Web-Apps ab
16,4; Die Berechtigungsaufforderung muss einer direkten Benutzeraktion folgen.

## REST-API

Authentifizierte Cookie-Sitzungen verwenden:

- `GET /api/v1/notifications/state`
- `PUT /api/v1/notifications/preferences`
- `POST /api/v1/notifications/subscriptions`
- `DELETE /api/v1/notifications/subscriptions/{subscription_id}`
- `POST /api/v1/notifications/test`

Automatisierungs-Bearer-Tokens können keine persönlichen Push-Geräte verwalten. Anfrage und
Antwortschemata sind Teil des eingecheckten OpenAPI-Vertrags.
