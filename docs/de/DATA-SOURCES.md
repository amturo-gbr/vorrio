# Produkt-, Barcode- und Preisdaten

Keine einzelne Datenbank vereint zuverlässig jeden Einzelhändler, jedes Handelsmarkenprodukt,
Barcode, Bild, Preis und Ablaufdatum. Vorrio behält bestätigte Haushaltsdaten als
die Autorität und Aufzeichnungsherkunft für jeden externen Wert.

## Offene Fakten

Die Barcode-Suche verwendet den aktuellen Open Facts v3-Produktendpunkt mit
`product_type=all`. Eine Anfrage kann Lebensmittel, Schönheit, Tiernahrung und Allgemeines abdecken
Produktdatensätze und kann einer Weiterleitung zum passenden Open Facts-Projekt folgen.
Die explizite Quittungsüberprüfung nutzt die offizielle Search-a-licious-Volltext-API für
echte Lebensmittelkandidaten.

Zu den nützlichen Feldern gehören Produktname, Marke, Bild, Packungsmenge, Kategorie usw
Produkttyp. Die Berichterstattung wird von der Community gepflegt und kann unvollständig oder falsch sein.
Vorrio behandelt ein Ergebnis daher als Vorschlag, bis der Haushalt es bestätigt
es.

Der Paketscanner konsultiert Open Facts nur für eine prüfsummengültige Retail-GTIN.
Der Bon-Workflow führt während der automatischen Analyse nie eine Suche durch. Wenn eine Person
Öffnet eine ungelöste Zeile, sendet Vorrio möglicherweise nur den normalisierten Produkttext
Volltextsuche und Anzeige von höchstens drei Datensätzen. Händler, Marke, Verpackung
und der Quittungs-Preis-Kontext werden lokal ausgewertet; Der Preis wird nicht als Preis behandelt
Kandidatenpreis, wenn die Quelle keinen angibt. Nach Bestätigung, Barcode,
Image, Marke, Verpackungsdaten und Händlerwortlaut werden lokal.

Datenbankinhalte werden unter ODbL wiederverwendet. Für Produktbilder kann CC BY-SA erforderlich sein
Zuschreibung. Vorrio speichert Quell-URL, Datenbanklizenz, Bildlizenz,
Attributions- und Abrufzeit mit importierten Metadaten.

Open Facts begrenzt das Lesen einzelner Produkte und ermöglicht höchstens zehn Suchen
Anfragen pro Minute und Quell-IP. Vorrio fragt daher nur Prüfsummengültigkeit ab
EAN-8-, UPC-A-, EAN-13- und GTIN-14-Werte während des Scannens, startet nur die Textsuche
Aus einer expliziten Überprüfung der Empfangszeile werden beide Pfade 30 Tage lang und nie zwischengespeichert
Verwendet die Remote-Suche als Typ-Ahead. Interne Zahlencodes bleiben lokal. Siehe
[Produktscan](BARCODE-SCANNING.md).

Search-a-licious-Abdeckung und Händler-Tags werden von der Community gepflegt. Ein Vermisster
Store-Tag bedeutet „unbekannt“ und nicht „bei diesem Händler nicht verfügbar“. Store-Kontext ist
daher eher ein Ranking-Hinweis als ein Ausschlussfilter.

## Offene Preise

Open Prices können Community-Beobachtungen liefern, die an Produkte und Standorte gebunden sind.
Es ist als optionale Vergleichsschicht gedacht, nicht als Autorität für die
tatsächlichen Einkauf des Haushalts. Bestätigte Empfangspreise bleiben primär und sind
Verfügbar über den Produktpreisverlaufs-Endpunkt und den schreibgeschützten Preis
Insights-Endpunkt mit Store und bekanntem Variantenkontext. Eigentlich nur Zeilen
verpflichtet, Vorrio-Aktien zu beteiligen. Die PWA nennt diese Werte historisch
Haushaltsbeobachtungen, da sie keinen aktuellen Regalpreis belegen,
Promotion oder Verfügbarkeit.

## GS1

GS1-Dienste können validieren, ob eine GTIN einem erwarteten Unternehmen zugeordnet ist.
Sie sind kein offener universeller Produktkatalog und haben Zugriffsbeschränkungen, so auch GS1
ein optionaler Validierungsadapter anstelle der Standardsuche.

## Ablaufdaten

Ein normaler EAN-13-Barcode kodiert kein Ablaufdatum. Vorrio akzeptiert eine genaue
Das Mindesthaltbarkeitsdatum entnehmen Sie bitte ausschließlich der Quittung, einem Etikettenscan oder einem unterstützten GS1 Digital
Link/2D-Anwendungskennung wie `15` oder `17`. Ansonsten ist das Produkt
Die standardmäßige Haltbarkeitsdauer bleibt ein editierbarer Planungswert und in vielen Fällen keine Tatsache.

## Empfehlungen des Analyseanbieters

Das ausgewählte Modell kann die Formulierung des Einzelhändlers normalisieren und einen lokalen Master vorschlagen
Daten. Genaue Preis-, Mengen-, Barcode-, Filial- und Datumswerte müssen aus dem stammen
Quittung oder Paket. Neue lokale Daten werden erst nach sichtbarer Bestätigung erstellt.
