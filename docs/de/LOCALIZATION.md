# Lokalisierung

Vorrio bietet eine vollständige deutsche und englische Benutzeroberfläche. Sprache ist etwas Persönliches
Kontopräferenz, keine haushaltsweite Bereitstellungseinstellung. Beginnend mit
0.8.23 ist jede offizielle Übersetzung auch ein versioniertes, reines Daten-Sprachpaket.
Der kleine deutsche Sicherheitsrückfall bleibt bestehen; andere Kataloge werden geladen
Nachfrage.

## Wie die Sprache ausgewählt wird

Vor der Anmeldung überprüft die PWA die letzte lokale Auswahl und dann den Browser
Sprache. `en-*` wird in Englisch aufgelöst, `de-*` in Deutsch und wird nicht unterstützt
Sprachen greifen auf Deutsch zurück. Die Erstausschreibungs- und Einladungsformulare senden dies
Wahl, wenn sie das Konto erstellen.

Nach der Anmeldung wird die serverseitige `preferred_locale` des aktuellen Kontos angezeigt
maßgeblich. Durch Ändern von **Einstellungen → Sprache und Region** wird die Auswahl gespeichert
über `PATCH /api/v1/auth/preferences` wird der aktuelle Bildschirm aktualisiert
sofort und wird beim nächsten Sitzungsladevorgang auf den anderen Geräten des Benutzers angewendet.
Wenn das Speichern fehlschlägt, stellt die PWA die vorherige Sprache wieder her und zeigt den Fehler an.

Die Präferenz akzeptiert die BCP 47-Basiswerte `de` und `en`. Es ist im Lieferumfang enthalten
die authentifizierte Benutzerantwort, tragbarer Export und vollständige Löschung. Es ist
Nicht verfügbar für Automatisierungs-Bearer-Token.

## Was lokalisiert ist

- alle authentifizierten und abgemeldeten PWA-Navigationen, Formulare, Dialoge, leer
  Status, Onboarding, Versionshinweise und clientseitige Validierung;
- Bekannte API-Fehler, die von der PWA angezeigt werden, einschließlich dynamischer Bereich, Bestand und
  nicht gefundene Nachrichten;
- Zahlen, Daten und EUR-Anzeige über das aktive Browser-Gebietsschema;
- API-Token-Bereichsbeschreibungen und vom Server generierte Web-Push-Benachrichtigungen;
- Deutsche und englische PWA-Manifeste.

Produktnamen, Marken, Quittungs-/OCR-Text, Geschäftsnamen und vom Benutzer eingegebene Stammdaten
Die Daten sind Haushaltsinhalte und werden niemals übersetzt. Vorrio auch nicht
Ändern Sie die konfigurierte Bereitstellungszeitzone oder die aufgezeichnete Währung einer Quittung
wenn sich die Sprache der Benutzeroberfläche ändert. Fehlertexte von Drittanbietern werden nicht angezeigt;
Die begrenzte Vorrio-Führung ist stattdessen in der PWA lokalisiert.

Schädliche Bestätigungsphrasen werden in der aktiven Benutzeroberfläche angezeigt
Sprache. Der Client validiert diese lokalisierte Phrase, sendet aber den Stable
kanonischer Bestätigungswert, der von der REST-API benötigt wird. Das hält die Öffentlichkeit
API deterministisch, ohne einen englischen Benutzer zu zwingen, deutsche Sicherheit einzugeben
Kopie.

Bei einer brandneuen Installation bestimmt die Setup-Sprache des Erstbesitzers die
Werkslagerorte, Einheiten und Produktgruppen. Diese Zeilen sind lokalisiert
bevor eine authentifizierte Katalogbearbeitung möglich ist. Sie werden sofort
normale Haushaltsdaten und werden niemals von einer späteren Schnittstellensprache umbenannt
ändern.

## Implementierungsvertrag

Jede gebündelte Sprache besitzt unten `manifest.json` und `translation.json`
`frontend/src/locales/<locale>/`. Das Zentralregister in
`frontend/src/locales/registry.ts` stellt den unterstützten Gebietsschematyp „nativ“ bereit
Label, Richtung, Vertrauensstufe, Vollständigkeit und Kataloglader. Die PWA wird eingebettet
Das kleine deutsche Sicherheits-Fallback lädt vorher eine andere ausgewählte Sprache
Rendern und Zwischenspeichern dieses unveränderlichen, inhaltsgehashten Teils für den späteren Offlinebetrieb
beginnt. Andere Sprachbrocken gehören nicht zum eifrigen Servicemitarbeiter
Vorcache. Wenn ein nie verwendetes Paket nicht abgerufen werden kann, bleibt das Startup weiterhin verwendbar
Deutsch und die Kontoeinstellung werden nicht überschrieben.

Die ursprünglichen deutschen Satzschlüssel bleiben dabei ein Kompatibilitäts-Fallback
werden nach und nach migriert. Neue Produktkopien verwenden stabile Namensraumschlüssel wie z
`language.interface_label`; CI verhindert die Anzahl der Legacy-Satzschlüssel
vom Zunehmen. Stabile Schlüssel müssen sowohl deutsche als auch englische Werte haben. Reagieren
Ansichten müssen `translate(...)` oder `useTranslation()` für sichtbare Produktkopien verwenden.

`frontend/src/i18n.ts` besitzt Gebietsschemaerkennung, Persistenz, Dokumentrichtung,
lokalisierte Manifestauswahl und Zahlen-/Datums-/Währungsformatierer. Die Sprache
Switcher verwendet den nativen Namen jedes Pakets, anstatt die Sprachnamen zu übersetzen
durch den aktuell aktiven Katalog.

Die Datenbank fügt `users.preferred_locale` mit einem sicheren `de`-Standardwert und a hinzu
`de`/`en` prüfen. Bestehende Konten werden ohne Änderung auf Deutsch migriert
Haushalts-, Quittungs-, Katalog- oder Bestandsdaten. Vom Server generierte persönliche Inhalte
liest immer das gespeicherte Gebietsschema des Zielbenutzers; Es darf niemals prozessweit eins verwendet werden
Sprache.

Führen Sie diese Prüfungen nach jeder Änderung der Benutzeroberfläche oder Lokalisierung durch:

```bash
cd frontend
npm test
npm run build
cd ..
make pwa-check
python3 scripts/validate_language_pack.py
make api-docs-check
```

`npm test` beinhaltet `scripts/check-i18n-contract.mjs`. Der Vertrag analysiert die
TypeScript/TSX-Quellen, schlägt wegen eines fehlenden oder leeren englischen Schlüssels fehl, erfordert
Deutsche und englische Singular-/Pluralformen für jede Count-Aware-Nachricht und
kennzeichnet eine wahrscheinlich sichtbare deutsche Kopie, die die Übersetzungsebene umgeht. Die
Der Sprachpaket-Validator lehnt außerdem unerwartete Dateien, ausführbare Dateien oder Dateien ab
HTML-Inhalt, unbekannte Schlüssel, leere Werte, geänderte Interpolationsplatzhalter,
ungültige Metadaten und Kataloge, die größer als 2 MiB sind.

## Offizielle und Community-Pakete

Offizielle Pakete werden überprüft, vervollständigt und im signierten Vorrio versendet
Behälter. Benutzer wählen sie direkt unter **Einstellungen → Sprache & Region** aus;
Es gibt kein separates Docker-Image oder eine separate Bereitstellungsvariable. Das aktuell
Der ausgewählte, nicht standardmäßige Block wird vom eigenen Vorrio des Benutzers heruntergeladen
Installation, kein Service eines Drittanbieters.

Das öffentliche Datenformat für zukünftige Community-Pakete ist in definiert
`language-packs/schema-v1.json`. Ein Quellpaket enthält nur ein Manifest und ein
flacher JSON-Katalog; Skripte, HTML, CSS, Binärdateien und Installations-Hooks sind niemals vorhanden
erlaubt. Community-Beiträge können bereits über den Validator und normal erfolgen
GitHub-Rezension. Die Laufzeitinstallation aus einem Paketindex bleibt bis deaktiviert
Vorrio kann einen von Amturo kontrollierten Index, Prüfsumme, Signatur und Kompatibilität überprüfen
Überprüfen Sie die Schema-/Anwendungsversionen und die Vollständigkeit, bevor Sie eine Sprache verfügbar machen
Benutzer. Details und Beitragsschritte live unter `language-packs/README.md`.
Der für den Mitwirkenden relevante Workflow für Problem, Überprüfung, Status und offizielle Werbung ist
gepflegt in [Übersetzungsgemeinschaft](TRANSLATION-COMMUNITY.md).

## Eine weitere Sprache hinzufügen

Das Hinzufügen einer Sprache ist eine explizite Produkt- und API-Änderung, nicht nur ein Katalog
Datei. Ein Beitrag muss zusammen aktualisiert werden:

1. Frontend- und Backend-Typen `SupportedLocale` plus Gebietsschemaerkennung;
2. ein vollständig überprüftes Manifest und ein Übersetzungskatalog;
3. länderspezifische Serverkopie für Versionshinweise, Token-Bereiche und Push;
4. ein lokalisiertes PWA-Manifest;
5. Einrichtungs-, Einladungs-, Präferenz-, Formatierungs- und Benachrichtigungstests;
6. der Sprachpaket-Validator, dieses Dokument, OpenAPI, Änderungsprotokoll und Release
   Notizen.

Bei der maschinellen Übersetzung kann zwar ein Entwurf erstellt werden, dieser muss jedoch von einem kompetenten Prüfer genehmigt werden
die komplette User Journey, insbesondere Sicherheit, Löschung, Lagerbewegung und
Empfangsbestätigungssprache.
