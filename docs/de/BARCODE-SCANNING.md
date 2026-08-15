# Produktscannen

Die Quittungsannahme und das Scannen von Paketen lösen unterschiedliche Aufgaben. Eine Quittung fügt a hinzu
gesamter Einkauf effizient; Ein Produktscan identifiziert ein physisches Paket für
Kataloganreicherung, Bestandskorrektur, Verbrauch oder die Einkaufsliste.
Vorrio 0.8.14 bietet beide als gleichwertige primäre Aktionen, die durch einen lokalen Katalog unterstützt werden.

## Einstiegspunkte

- eine prominente **Scannen**-Aktion in der Mobil- und Desktop-Navigation;
- Live-Kamerascan auf Telefonen, Tablets und mit Kameras ausgestatteten Computern;
- ein fokussiertes Feld für USB-, Bluetooth- und 2,4-GHz-Scanner, die sich wie ein verhalten
  Tastatur eingeben und mit Enter absenden;
- manuelle Codeeingabe als zugänglicher Fallback;
- später derselbe Vertrag hinter nativen iOS- und Android-Scanner-Plugins.

Der Benutzer wählt vor dem Scannen die gewünschte Aktion aus:

| Modus | Ergebnis nach Bestätigung |
|---|---|
| Identifizieren | Zeigen Sie Produkt-/Variantenmetadaten an und bestätigen Sie diese bei Bedarf, ohne die Lagerbestandsmenge zu ändern. |
| Lagerbestand hinzufügen | Fügen Sie eine Menge, einen optionalen Preis, einen Standort und ein Mindesthaltbarkeitsdatum hinzu. |
| Konsumieren | Reduzieren Sie den verfügbaren Bestand durch reine Anhängebewegungen. |
| Öffnen | Markieren Sie ein entsprechendes vorhandenes Los als geöffnet. |
| Einkaufsliste | Fügen Sie den nicht markierten Artikel für das generische Produkt hinzu oder erhöhen Sie ihn. |

Der Modus ist immer sichtbar und seine Wirkung wird im Klartext erklärt. A
Ein einziges zugängliches Steuerelement **Erklärte Aktionen** öffnet alle fünf Erklärungen in
ein mobiles unteres Blatt oder ein zentrierter Desktop-Dialog; der ausgewählte Modus ist
hervorgehoben und kein verschachteltes Hilfeziel stört die Aktionsregisterkarten. Die
Der Dialog fängt den Tastaturfokus ein, wird mit Escape oder seinen expliziten Steuerelementen geschlossen und
stellt den Fokus wieder auf den Auslöser. Auf einem Telefon funktionieren alle fünf Aktionen auch ohne
horizontales Scrollen. Sobald ein Code aufgelöst wird, verlässt das Erfassungsfeld den
Auf dem Bildschirm wird die Rezension zum Hauptinhalt und die letzte Aktion bleibt bestehen
erreichbar über mobile Navigation. Es wird ein kurzes Erfolgs-/Fehler-Audio-Feedback verwendet
wenn der Browser dies zulässt.
Stationsspezifische angeheftete Standardeinstellungen und ein Rückgängig-Fenster bleiben zukünftige Verbesserungen.

## Offline-Warteschlange

Die installierte PWA kann ihre zwischengespeicherte Shell auf einem Gerät erneut öffnen, das einen abgeschlossen hat
erfolgreiche Anmeldung im Haushalt, bevor Sie offline gehen. Ein Scan ohne Server
Die Verbindung speichert nur den normalisierten Eingabecode, die beabsichtigte Aktion und den Zeitstempel
und eine stabile Client-Mutations-ID im lokalen Speicher dieses Browsers.

- Kein Passwort, kein Sitzungscookie, keine Katalogzeile, kein Produktbild oder kein Quittungsinhalt
  in die Warteschlange kopiert;
- Es findet keine Suche, Produktzuordnung, Lagerbewegung oder Änderung der Einkaufsliste statt
  offline;
– Das gleiche Barcode-/Aktionspaar wird einmal in die Warteschlange gestellt und die Warteschlange wird bei 100 nicht geschlossen
  Einträge, anstatt einen älteren Scan zu verwerfen;
- ausstehende Zeilen sind sichtbar und können lokal entfernt werden;
- erneut verbinden oder **Jetzt abgleichen** versucht die ursprüngliche idempotente Auflösung erneut
  Anfrage, dann öffnet sich die normale Rezension; Die Bestätigung bleibt zwingend erforderlich.

Bei einem Authentifizierungsfehler während der Synchronisierung bleiben alle ausstehenden Zeilen aktiviert
das Gerät und fordert den Haushalt auf, sich erneut anzumelden. Die lokal authentifizierte
Der Gerätehinweis entsperrt nur die zwischengespeicherte Shell und Warteschlange. es wird von der nicht akzeptiert
Server als Authentifizierung.

## Auflösungsreihenfolge

1. Behalten Sie die Roheingabe bei, normalisieren Sie Trennzeichen und validieren Sie unterstützte numerische Werte
   Längen und GTIN-Prüfsummen. Platzhalter-GTINs mit wiederholten Ziffern, z. B
   Fehlalarme mit einer Kamera, bei denen es sich ausschließlich um Nullen handelt, werden abgelehnt, bevor ein Entwurf erstellt wird.
2. Suchen Sie zuerst nach `catalog_barcodes` und lokalen Varianten.
3. Suchen Sie nach prüfsummengültigen EAN-8-, UPC-A-, EAN-13- und GTIN-14-Werten
   Externer Datensatz zwischengespeichert in `catalog_external_refs`.
4. Fragen Sie den universellen Open Facts v3-Produktendpunkt mit ab
   `product_type=all`, wenn eine solche Einzelhandels-GTIN kein aktuelles lokales/Cache-Ergebnis hat.
   Andere numerische Codes bleiben lokal und werden niemals an einen externen Katalog gesendet.
5. Präsentieren Sie Name, Marke, Menge, Bild, Kategorie, Produkttyp, Quelle und
   Namensnennung als bearbeitbare Vorschläge.
6. Wenden Sie keine Lager- oder Einkaufsmutation an, bis der Benutzer das Produkt bestätigt und
   ausgewählte Aktion.
7. Werten Sie nach der Bestätigung nicht aufgelöste Wareneingangszeilen lokal neu aus. Genau
   Barcode-, Alias- oder Namensübereinstimmungen können möglicherweise aufgelöst werden. Unscharfe Namen bleiben Vorschläge.

Bestätigte Haushaltswerte bleiben maßgebend. Externe Metadaten füllen ein neues
Variante oder ein leeres lokales Feld erst nach sichtbarer Bestätigung; es nie
benennt ein bestätigtes Produkt stillschweigend um, verschiebt Lagerbestände oder ändert die Haltbarkeit.

## Bekannte und unbekannte Codes

Ein bekannter lokaler Code zeigt das Produkt, die konkrete Variante, den aktuellen Lagerbestand und die Aktion an
in einem Bewertungsgremium.

Ein nur externes Ergebnis bleibt ungelöst, bis der Haushalt es entweder kartiert
zu einem vorhandenen generischen Produkt oder bearbeitet und bestätigt ein neues Produkt/eine neue Variante.
Standort, Einheit und Produktgruppe nutzen die aktuellen lokalen Stammdatenlisten.

Ein unbekannter Code wird niemals stillschweigend verworfen. Es werden **Unbekannte Codes** eingegeben
mit Zeitstempel und vorgesehenem Modus. Der Haushalt kann es kartieren, ein Produkt erstellen oder
den Entwurf absichtlich verwerfen. Wiederholte ungelöste Scans desselben Codes und
Modus denselben Entwurf wiederverwenden. Optionale Front-/Etikettfotos sind nicht Teil von 0.8.14.

## Kamera- und Hardwarescanner

Die PWA verwendet `getUserMedia` in einem sicheren Kontext und lädt das Paket verzögert
`@zxing/browser` eindimensionaler Produktcode-Decoder. Kamerarahmen bleiben erhalten
im Browser; Es wird nur die entschlüsselte Zeichenfolge übermittelt. Eine Kamera
Das Ergebnis muss in zwei benachbarten Bildern identisch beobachtet werden, bevor Vorrio anhält
die Vorschau und löst sie auf. Dies schützt den nicht aufgelösten Posteingang vor vorübergehenden Zugriffen
Einzelbild-False-Positives ohne Verlangsamung der Tastaturscanner.

Für das Live-Kamera-Scannen ist daher HTTPS (oder ein vom Browser definierter Localhost) erforderlich
Ausnahme), keine unformatierte LAN-HTTP-Adresse. Fehlt diese Anforderung, gilt die
Die Benutzeroberfläche erklärt es und macht manuelle und Hardware-Scanner-Eingaben nutzbar.

Tastatur-Wedge-Scanner benötigen kein spezielles Protokoll. Platzieren Sie den Cursor im Code
Geben Sie das Feld ein, scannen Sie es und lassen Sie das Enter-Suffix des Scanners senden. Kurze interne Zahl
Codes können genau wie Barcodes im Einzelhandel lokal zugeordnet werden, werden aber bewusst übersprungen
Externe Produktsuche. Gerätespezifische Präfixe und Suffixe sind nicht vorhanden
konfigurierbar in 0.8.14.

## REST-Vertrag

Die authentifizierten versionierten Ressourcen sind:

- `POST /api/v1/scans/resolve` für idempotente lokale/cache/external-Auflösung;
- `GET /api/v1/scans/{scan_id}`, um einen Entwurf zu lesen;
- `POST /api/v1/scans/{scan_id}/confirm` für die ausgewählte Aktion;
- `GET /api/v1/scans/unresolved` für den Bewertungsposteingang;
- `PATCH /api/v1/scans/{scan_id}` zum Ändern des Modus, der Zuordnung oder des Vorschlags;
- `DELETE /api/v1/scans/{scan_id}`, um einen ungelösten Entwurf als verworfen zu markieren;
- `GET /api/v1/shopping-list` zum Lesen ungeprüfter Haushaltslistenelemente;
- `GET /api/v1/shopping-list/low-stock` zur Vorschau der aktuellen Nachfüllregeln;
- `POST /api/v1/shopping-list/generate` zur Bestätigung ausgewählter Vorschläge;
- `PATCH /api/v1/shopping-list/{item_id}`, um einen Artikel zu ändern oder zu vervollständigen;
- `POST /api/v1/catalog/reconcile`, um offene Empfangszeilen erneut zu überprüfen
  den lokalen Katalog und gelernte Zuordnungen.

Lösen und bestätigen Sie die Annahme separater, vom Client generierter Idempotenzschlüssel. Ein erneuter Versuch
mit demselben Schlüssel gibt den ursprünglichen Entwurf/die ursprüngliche Aktion zurück.

Beispielsuche:

```http
POST /api/v1/scans/resolve
Content-Type: application/json

{
  "barcode": "4006381333931",
  "mode": "add",
  "client_mutation_id": "scan_018f3f1c8c1a"
}
```

Beispielbestätigung für eine bestehende lokale Übereinstimmung:

```http
POST /api/v1/scans/SCAN_ID/confirm
Content-Type: application/json

{
  "client_mutation_id": "confirm_018f3f1c8c1a",
  "quantity": 2,
  "location_id": 1,
  "best_before_date": "2026-09-30"
}
```

Die vollständigen Schemata, Grenzen und Fehler werden unter `/docs`, `/redoc` und generiert
`/openapi.json`.

## Aktionssemantik

- **Identifizieren** ändert keine Bestandsmenge.
- **Lagerbestand hinzufügen** erstellt ein Los und eine positive `scan_add`-Bewegung.
- **Consume** validiert zuerst die Gesamtverfügbarkeit und zieht davon ab
  Die am frühesten ablaufenden Lose, dann die ältesten Lose mit negativen Bewegungen.
- **Offen** markiert die früheste entsprechende ungeöffnete Charge und zeichnet einen Nullwert auf
  `scan_open` Bewegung.
- **Einkaufsliste** verwendet einen ungeprüften Artikel für dasselbe Produkt wieder und erhöht ihn
  die gewünschte Menge. Die Mindestbestandsgenerierung verwendet denselben Artikel und niemals
  senkt eine größere Wunschmenge.

## Datenschutz und Verfügbarkeit

- Raw-Kamerabilder bleiben auf dem Gerät und 0.8.14 lädt keine Paketfotos hoch.
- Kameralesungen sind auf eindimensionale Produktcodes beschränkt; QR und Micro QR
  Muster werden vom Paketscanner bewusst ignoriert.
- Wenn die lokale und zwischengespeicherte Suche fehlschlägt, wird nur eine prüfsummengültige EAN/UPC/GTIN gesendet
  Fakten offenlegen; Interne Codes bleiben in der Installation. Das Ergebnispanel
  identifiziert jede externe Quelle.
- Die Ergebnisse werden mit Provenienz zwischengespeichert, um den Grenzdruck zu reduzieren und zu reduzieren
  Wiederholen Sie Scans schnell.
- Externe Ausfälle gehen auf einen lokalen ungelösten Entwurf zurück und scheitern nicht
  den kompletten Scan-Workflow.
– Scanner-/Dienstkonten erhalten später bereichsbezogene Token statt kopierter menschlicher
  Browsersitzungen.

## Technische Referenzen

- [Open Facts universelle Produktsuche](https://openfoodfacts.github.io/documentation/docs/Product-Opener/api/tutorials/scanning-cosmetics-pet-food-and-other-products/)
- [Open Facts v3-Produktendpunkt](https://openfoodfacts.github.io/documentation/docs/Product-Opener/v3/products/get-api-v3-product-code/)
- [ZXing Browser-Kamera-Decoder](https://github.com/zxing-js/browser)
- [MDN Secure-Context-Medienzugriff](https://developer.mozilla.org/en-US/docs/Web/API/MediaDevices/getUserMedia)
