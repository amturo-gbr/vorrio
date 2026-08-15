# Übersetzungsgemeinschaft

Vorrio begrüßt rein datenbasierte Sprachbeiträge über GitHub. Übersetzer
Sie müssen keinen Haushaltsserver betreiben, keinen Anwendungscode bearbeiten oder Zugriff erhalten
an ein Amturo-System. Übersetzungsbeispiele und Screenshots müssen synthetisch sein
Daten.

## Beitragsstufen

| Bühne | Bedeutung | Wählbar in Vorrio |
|---|---|---|
| Angefordert | Eine Ausgabe erfasst Interesse, Standort und mögliche Mitwirkende. | Nein |
| In Bearbeitung | Ein Mitwirkender besitzt einen Entwurf unter `language-packs/community/`. | Nein |
| Community-Kandidat | Das reine Datenpaket besteht technische Prüfungen und kann schrittweise überprüft werden. | Nein |
| Verifizierte Community | Vollständiger Katalog mit unabhängiger fließender Rezension, der auf die Produktintegration wartet. | Nein |
| Offiziell | Integriert in Frontend, Backend, Benachrichtigungen und Installationsmetadaten und wird dann in einer signierten Vorrio-Version ausgeliefert. | Ja |

Der Community-Status ist kein niedrigerer Sicherheitsmodus. Jedes Paket ist immer noch reines JSON
und müssen die gleichen Inhalts-, Größen- und Platzhalterregeln erfüllen. Es beschreibt nur
Vollständigkeit der Übersetzung und Reife der Rezension.

## Starten Sie eine Sprache

1. Suchen Sie nach offenen Problemen für das Gebietsschema und öffnen Sie das Problem **Neue Sprache**, wenn
   keine existiert. Eine Ausgabe koordiniert Übersetzer und unabhängige Gutachter.
2. Verzweigen Sie das Repository, erstellen Sie einen Zweig und generieren Sie das Paketskelett:

   ```bash
   python3 scripts/create_language_pack.py es "Español" "Spanish"
   ```

   Verwenden Sie `--direction rtl` für eine von rechts nach links geschriebene Sprache oder ein regionales BCP 47-Tag
   wie zum Beispiel `pt-BR`, wenn die Terminologie tatsächlich unterschiedlich ist.
3. Fügen Sie Übersetzungen hinzu
   `language-packs/community/<locale>/translation.json`. Der englische Katalog unter
   `frontend/src/locales/en/translation.json` ist die kanonische Quelle. Fehlt
   Community-Einträge greifen bei der Erstellung des Entwurfs bewusst auf Englisch zurück
   außerhalb der Laufzeit.
4. Aktualisieren Sie `completion` in `manifest.json` auf den gerundeten kanonischen Prozentsatz
   Schlüssel explizit vorhanden. Der Prüfer lehnt einen ungenauen Prozentsatz ab.
5. Ausführen:

   ```bash
   python3 scripts/validate_language_pack.py language-packs/community/es
   make language-pack-check
   ```

6. Commit mit DCO-Abzeichnung und Öffnen einer Pull-Anfrage mit dem **Sprachpaket**
   Vorlage. Verknüpfen Sie das Sprachproblem und legen Sie alle maschinengestützten Entwürfe offen.

Der Generator weigert sich, ein vorhandenes Verzeichnis zu ersetzen. Eine Packung enthält nur
`manifest.json` und `translation.json`; Bilder, Skripte, Stile, Binärdateien und
Installations-Hooks werden abgelehnt.

## Verantwortlichkeiten überprüfen

| Verantwortung | Übersetzer | Fließender Rezensent | Amturo-Betreuer | Automatisierung |
|---|---:|---:|---:|---:|
| Regionale Terminologie übersetzen und erklären | Ja | Bewertungen | Beobachtet | Nein |
| Überprüfen Sie die natürliche Sprache und den Haushaltsvokabular | Selbstbewertung | Ja | Verifiziert Beweise | Nein |
| Login, Sicherheit, Löschung und Bestandsbedeutung prüfen | Selbstbewertung | Ja | Erfordert Überprüfung | Strukturprüfungen |
| JSON, Platzhalter, Dateien und Vollständigkeit validieren | Optional lokal | Optional lokal | Bestätigt CI | Ja |
| Entscheiden Sie sich für den Gemeinschafts- oder offiziellen Status | Schlägt vor | Empfiehlt | Ja | Nein |
| Ein signiertes Release zusammenführen, integrieren und veröffentlichen | Nein | Nein | Ja | Erforderliche Tore |

Der offizielle Status erfordert eine Genehmigung des technischen Betreuers und mindestens eine
unabhängiger, fließend sprechender Rezensent, der nicht die vollständige Übersetzung verfasst hat. Sicherheit,
Wiederherstellung, destruktive Löschung, Empfangsbestätigung und Bestandsbewegungskopie
erhält vor der Veröffentlichung eine zweite unabhängige Sprachprüfung. Wenn es Rezensenten sind
nicht verfügbar, ein technisch gültiges Paket kann ein Community-Kandidat bleiben
ohne den Benutzern ausgesetzt zu sein.

Durch maschinelle Übersetzung kann ein offengelegter Entwurf erstellt werden. Es kann nicht als Gutachter fungieren
oder einen verifizierten oder offiziellen Status gewähren.

## Betreuer-Workflow

Betreuer wenden diese Problem-/PR-Kennzeichnungen an oder erstellen sie:

- `language:requested`
- `language:in-progress`
- `language:needs-review`
- `language:verified`
- `language:official`

Bevor Sie einen Community-Kandidaten zusammenführen, bestätigen Sie, dass das Problem verknüpft ist, und geben Sie die Freigabe durch den DCO ab
vorhanden ist, die Fachcheckliste vollständig ist und CI das Paket validiert.
Durch das Zusammenführen des Nur-Daten-Kandidaten wird dieser nicht auswählbar.

Die Beförderung zum Beamten ist eine separate Produkt-Pull-Anfrage. Es registriert die
Gebietsschema, vervollständigt gebietsschemabezogene Backend-Nachrichten und -Benachrichtigungen und fügt PWA hinzu
Metadaten installieren, Tests und Dokumentation aktualisieren und `make check` bestehen.
Das offizielle Paket wird erst im nächsten signierten Bild verfügbar. Willkürlich
Laufzeit-Downloads bleiben deaktiviert, bis Vorrio eine signierte, mit Prüfsummen versehene Datei hat
versionkompatibler Amturo-Paketindex.

Git-Verlauf und Versionshinweise erwähnen die Mitwirkenden. Übersetzungspakete tun dies nicht
enthalten ausführbare Namensnennungen oder persönliche Metadaten, und Mitwirkende sollten dies nicht tun
E-Mail-Adressen veröffentlichen, die über die DCO-Identität hinausgehen, die sie absichtlich verwenden.

Alle Beiträge folgen dem [Verhaltenskodex](https://github.com/amturo-gbr/vorrio/blob/main/CODE_OF_CONDUCT.md),
[Beitragsleitfaden](https://github.com/amturo-gbr/vorrio/blob/main/CONTRIBUTING.md),
[Governance](GOVERNANCE.md) und die
[Sprachpaketvertrag](https://github.com/amturo-gbr/vorrio/blob/main/language-packs/README.md).
