# Haushaltsbudget

Vorrio 0.8.14 fügt unten ein gemeinsames, belegbasiertes Monatsbudget hinzu
**Einkaufen → Budget**. Es ist bewusst unabhängig von Bankkonten und
stellt historische Quittungswerte niemals als Live-Händlerpreise dar.

## Datenquelle und Zählregel

Eine Quittung trägt ihre Gesamtsumme nur dann bei, wenn alle diese Bedingungen erfüllt sind
wahr:

- Mindestens eine seiner Zeilen wurde ausdrücklich überprüft und Vorrio übergeben
  Lager;
- seine Summe ist vorhanden und größer als Null;
- seine Währung ist EUR;
- sein Kaufdatum, oder alternativ das Belegerstellungsdatum, liegt im
  Berichtszeitraum.

Ein ungelöster oder lediglich analysierter Beleg kann einen Budgetwert nicht ändern. A
ein bestätigter Empfang ohne verwertbaren Gesamtbetrag und ein bestätigter Nicht-EUR-Beleg sind
gesondert ausgewiesen, statt stillschweigend gezählt zu werden. Quittungen warten noch
Überprüfung werden ebenfalls als ausstehend angezeigt.

Diese Version unterstützt einen Haushalt pro Installation. Das Budget also
verwendet den Empfangsverlauf dieser Installation und eine gemeinsame Haushaltseinstellung.
Für die Unterstützung mehrerer Haushalte ist auf jeder Quittung und jedem Haushaltseigentum zu achten
Bestandsdomänentabelle, bevor diese Grenze sicher erweitert werden kann.

## Metriken

Die Übersicht ergibt:

- bestätigte monatliche Ausgaben und gezählte Einnahmen;
- verbleibendes Monatsbudget und verwendeter Prozentsatz;
- verbleibende Kalendertage und eine Orientierung pro Tag;
- eine einfache Vorhersage im Kalendertempo: `spent / elapsed days × days in month`;
- Stichtag am selben Tag des vorangegangenen Kalendermonats;
- bis zu 24 Monatssummen, wobei sechs Monate von der PWA genutzt werden;
- Aktien des aktuellen Monats, gruppiert nach normalisiertem Einzelhändler;
- bestätigte, gezählte, ausstehende, fehlende Gesamt- und andere Währungszählungen.

Die Prognose ist Orientierung, keine Vorhersage. Es modelliert nicht den Zahltag,
Wochenenden, wiederkehrende Einkäufe, Feiertage oder zukünftige Werbeaktionen. Wenn keine Quittung vorliegt
gezählt wurde, zeigt die PWA keinen Prognosewert an.

## Einstellungen und Berechtigungen

Eigentümer und Administrator können ein monatliches EUR-Limit zwischen 1 und 1.000.000 EUR festlegen
und eine Warnschwelle von 50 bis 100 Prozent. Mitglieds- und Zuschauerkonten können
Sie können die gemeinsame Übersicht lesen, das Ziel jedoch nicht ändern. Entfernen des Ziels
löscht nur die Einstellung; Quittungen, Produkte, Lagerbestände und historische Zusammenfassungen bleiben erhalten
unberührt.

Browsersitzungen sind erforderlich. Mit bereichsbezogenen Automatisierungstoken ist kein Zugriff oder keine Änderung möglich
das Haushaltsbudget im Jahr 0.8.14. Durch eine Einstellungsänderung wird ein Sicherheitsüberwachungsereignis erstellt
das den Haushalt, den konfigurierten Zustand und den Warnprozentsatz aufzeichnet, aber nicht
die rohe Geldgrenze.

## REST-API

- `GET /api/v1/insights/budget?months=6` gibt die Übersicht für 1–24 Monate zurück.
- `PUT /api/v1/insights/budget/settings` legt das gemeinsame Ziel fest oder löscht es.

Die Anforderungs- und Antwortschemata sind im eingecheckten Zustand kanonisch
[OpenAPI-Vertrag](../api/openapi.json) und gerendert von `/docs` und `/redoc` auf a
laufende Installation.

## Bewusste Grenzen setzen

- Keine Bankverbindung oder Finanzkontodaten.
- Nur EUR, bis Währungsumrechnung und Haushaltsgebietsregeln explizit festgelegt sind.
- Kein automatisches Budgetziel, das aus der privaten Beleghistorie abgeleitet wird.
- Kein externer Live-Preisvergleich, bis eine lizenzierte, vertrauenswürdige Quelle dies kann
  Bereitstellung des aktuellen Produkt-, Branchen-, Paket- und Verfügbarkeitskontexts.
- Kein unbeaufsichtigter Kauf oder keine Änderung der Einkaufsliste aus der Budgetansicht.
