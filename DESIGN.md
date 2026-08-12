# Designsystem

Die verbindlichen Vorrio-Konzepte liegen unter:

- `docs/design/home-concept.png`
- `docs/design/review-concept.png`
- `docs/design/review-safe-suggestions-mobile-0.4.0.png`
- `docs/design/master-data-review-0.5.0.png`
- `docs/design/master-data-review-mobile-0.5.0.png`
- `docs/design/scanner-desktop-concept-0.7.0.png`
- `docs/design/scanner-desktop-final-0.7.0.png`
- `docs/design/scanner-mobile-concept-0.7.0.png`
- `docs/design/scanner-mobile-final-0.7.0.png`
- `docs/design/scanner-entry-mobile-final-0.8.5.png`
- `docs/design/scanner-review-mobile-final-0.8.5.png`
- `docs/design/receipt-product-resolution-mobile-0.7.1.png`

Das gefaltete Bon-Asset liegt unter
`frontend/public/assets/receipt-folded.png`.

## Visuelle Idee

Ruhige, vertrauenswürdige Haushalts-App mit einem wiederkehrenden
Papierbon-/Faltmotiv. Die Oberfläche bleibt bewusst einfach:
eine primäre Aufgabe pro Ansicht, große Touch-Ziele und keine technischen
Begriffe im normalen Ablauf.

Vorrio ist nicht nur eine Smartphone-Oberfläche. Ab `960px` verwendet die
Web-App eine feste Seitenleiste, breite Arbeitsflächen und sinnvolle
Mehrspaltenlayouts. Darunter bleibt sie dieselbe installierbare PWA mit
horizontal erreichbaren Aktionsleisten und einer festen unteren Navigation.

## Tokens

| Rolle | Wert |
|---|---|
| Hintergrund | `#ffffff` |
| Text | `#182128` |
| Gedämpfter Text | `#6d7277` |
| Primärgrün | `#176b35` |
| Dunkles Primärgrün | `#10592b` |
| Helles Grün | `#eef7ed` |
| Prüfhinweis | `#f0644b` |
| Heller Prüfhinweis | `#fff5f1` |
| Ähnlichkeitsvorschlag | `#987119` |
| Heller Ähnlichkeitsvorschlag | `#fffbef` |
| Linie | `#dfe3df` |
| Fläche | `#f7f8f6` |
| Radius klein/mittel/groß | `12px / 16px / 20px` |
| Fokus-Ring | `0 0 0 3px rgba(23, 107, 53, .2)` |

## Typografie

- UI: `Inter`, `SF Pro Text`, `Segoe UI`, sans-serif;
- Überschrift: 700–760, enge Laufweite;
- Fließtext: 400–500;
- Button/Navigation: 650–700;
- Browser-Standardgrößen werden für Controls nicht verwendet.

## Container-Modell

- offene weiße Seiten statt eines Card-Grids;
- genau ein dominanter Kamera-Rahmen auf der Startseite;
- Einkäufe und Artikel als klare Listen mit Trennlinien;
- nur ungeklärte Zeilen erhalten eine farbige Umrandung;
- ein amberfarbener Zustand trennt prüfpflichtige Namensvorschläge klar von
  roten, vollständig ungeklärten Zeilen;
- die Importaktion bleibt mobil am unteren Rand sichtbar.

## Komponenten

- `AppHeader`: Marke, Verbindung und Zurück-Navigation;
- `CapturePanel`: Bonmotiv, Kamera- und Upload-Aktion;
- `ImportedReceiptState`: grüner Abschlussstatus, gesperrte Zeilen und getrennte
  Darstellung von Warenwert sowie Pfand/sonstigen Bonposten;
- `PurchaseRow`: letzter Einkauf mit Status;
- `ReceiptItemRow`: erkanntes Produkt, optionales Produktbild,
  Varianten-/Packungsdaten, Preis und ein kurzer erklärbarer Treffergrund;
- `MissingMasterSuggestion`: amberfarbener, editierbarer KI-Vorschlag für
  fehlende Lagerorte, Einheiten oder Produktgruppen; daneben bleiben die
  vollständigen vorhandenen Werte im Select sichtbar;
- `BottomNavigation`: Start, Vorrat, Einkäufe, Einstellungen;
- `StickyImportBar`: Summe und bestätigter Import;
- `ConnectionPanel`: URL, Schlüssel, Modell und Verbindungstest;
- `ScannerScreen`: fünf stets sichtbare Scan-Modi mit verständlicher
  Wirkungsbeschreibung, lokaler Kamera-Decoder, manuelle/Keyboard-Eingabe,
  bestätigungspflichtige Produktzuordnung und Unbekannt-Code-Inbox. Vor der
  Erkennung stehen Kamera und Eingabe im Fokus; danach ersetzt die Prüfung die
  Aufnahmefläche und hält die Bestätigung mobil erreichbar;
- `CatalogScreen`: offene Produktliste mit Bestand und Packungsanzahl;
  Produktdetails erscheinen mobil als großes Bottom-Sheet und auf Desktop als
  zentrierter Arbeitsdialog. Varianten und Barcodes bleiben klar untergeordnet;
- `MasterDataManager`: drei ruhige Listen für Lagerorte, Einheiten und Gruppen,
  jeweils mit Nutzungszahl, sichtbarer Bearbeitung und geschütztem Archivieren;
- `StatusMessage`: zugängliche Erfolg-, Hinweis- und Fehlerzustände.

## Icon-Inventar

Alle Icons sind abgerundet, linear, circa `1.8px` stark und werden aus einer
einheitlichen Lucide-Familie bezogen: Bon, Kamera, Upload, Start, Verlauf,
Einstellungen, Pfeil, Check, Warnung, Suche, Verbindung und Löschen.

## Sichtbarer Text im ersten Viewport

- `Vorrio`
- `Eigener Katalog` und gegebenenfalls der optionale Grocy-Verbindungsstatus
- `Einkauf übernehmen`
- `Bon fotografieren – Vorrio bereitet Bestand und Preise vor.`
- `Bon fotografieren`
- `Bild oder PDF hochladen`
- `Letzte Einkäufe`
- `Start`, `Vorrat`, `Einkäufe`, `Einstellungen`

Diese Liste ist die Copy-Sperre für die Startansicht. Neue technische Hinweise
werden nur kontextabhängig als Fehler- oder Einrichtungszustand gezeigt.
