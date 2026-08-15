# Haushaltsarbeitsablauf

## Konten, Familie und Geräte

Bei Neuinstallationen wird beim Festlegen des Haushaltspassworts der erste Eigentümer benannt.
Nach einem Upgrade funktionieren das vorhandene Passwort und der angemeldete Browser weiterhin; die
Die hervorgehobene Karte **Einstellungen → Eigentümer & Sicherheit** vervollständigt das Lokal
Anzeigename und optionale E-Mail-Adresse, ohne die Haushaltsdaten zu ändern.

Bei jeder Anmeldung wird eine separate 30-tägige serverseitige Browsersitzung erstellt. Die Einstellungen
Die Karte listet eine datenschutzsichere Browser-/Gerätebezeichnung und die letzte Aktivität auf. Eine Reihe kann sein
sofort widerrufen, oder **Andere Geräte abmelden** kann nur den aktuellen Stand behalten
Browser. Durch das Widerrufen der aktuellen Zeile wird zur Anmeldung zurückgekehrt.

Bevor der Eigentümer jemanden einlädt, speichert er eine eindeutige lokale E-Mail. Unter **Konto &
Familie**, Eigentümer oder Administrator gibt einen Namen, eine E-Mail-Adresse und eine zulässige Rolle ein. Das Ergebnis
Link läuft nach 72 Stunden ab und funktioniert einmal; Der Empfänger wählt einen Unabhängigen
Passwort. Der Administrator kann keine Administratorrechte gewähren oder Besitzer-/Administratorkonten ändern. Blockieren eines
Das Konto meldet es bei der nächsten Anfrage ab. Mit mehreren aktiven Benutzern, jeder
Meldet sich mit E-Mail und Passwort an. Erholung und MFA bleiben spätere Meilensteine.

## Quittungsaufnahme

1. Fotografieren Sie eine Quittung oder laden Sie ein Bild/PDF hoch.
2. Vorrio ermittelt Händler, Datum, Zeilen, Mengen und Preise.
3. Gelernte Formulierungen, bestätigte Aliase, lokale Barcodes und genaues lokales Produkt
   Namen werden automatisch mit einer sichtbaren Erklärung abgeglichen.
4. Fuzzy-Vorschläge bleiben bis zur Bestätigung gelb. Öffnen einer ungelösten Zeile
   sucht explizit nach bis zu drei realen, bildgestützten Produktkandidaten.
5. Vorrio ordnet die Kandidaten nach Name, Marke, Verpackung und Angaben zum Händler. Wenn ein
   Wenn der Anbieter konfiguriert ist, kann er nur diese echten Datensätze neu anordnen. es kann nicht
   Erstellen Sie ein anderes Produkt oder Bild.
6. Durch die Auswahl eines bekannten Kandidaten wird dieser mit dem vorhandenen lokalen Produkt verknüpft. Ein neues
   Der Kandidat öffnet ein bearbeitbares Formular mit dem vollständigen vorhandenen Standort.
   Einheiten- und Produktgruppenlisten.
7. Die Bestätigung speichert den Barcode, das Bild und die Paketvariante und lernt die
   Formulierung für diesen Einzelhändler. Die gleiche Wahl kann andere offene Leitungen auflösen.
8. Bestätigte Positionen werden einmalig dem lokalen Lagerbestand zugewiesen.
9. Ein aktivierter Grocy-Connector kann nachträglich verknüpfte Leitungen spiegeln.

Ein Verbindungsfehler führt niemals dazu, dass eine erfolgreiche lokale Aufnahme entfernt wird. Es wird angezeigt als
ein separates wiederholbares Ergebnis.

## Produkt und Variante

Verwenden Sie für das Haushaltskonzept ein generisches Produkt, beispielsweise „Milch“. Ein Beton
Marke, Packungsgröße und Barcode gehören zu einer Variante. Mehrere Varianten können
Teilen Sie ein Lager- und Einkaufskonzept.

Ein Produktbild kann optional aus einem bestätigten externen Produktdatensatz stammen
HTTP(S)-Adresse oder ein Haushaltskamera-/Datei-Upload. Lokale Uploads akzeptieren JPEG,
PNG und WebP werden orientiert, auf maximal 1600 Pixel pro Kante verkleinert und gespeichert
als metadatenfreies WebP. Sie werden nur über die authentifizierte API bereitgestellt. Die
Der Katalog erwähnt Grocy nur dann als Onboarding-Option, wenn dieser Connector vorhanden ist
aktiviert; Ansonsten bleibt Vorrio völlig eigenständig.

Für die Quittungsaufnahme ist kein Barcode erforderlich. Scannen Sie ein Paket später, um es anzureichern oder
Erstellen Sie seine Variante. Nach der Bestätigung überprüft Vorrio den ungelösten älteren Beleg erneut
Linien und kann einen genauen Barcode oder ein bereits bekanntes Produkt automatisch verbinden.
Lokale Übereinstimmungen werden vor externen Open-Facts-Daten überprüft.

Die Produkterkennung wird erst ausgeführt, nachdem eine Person eine bestimmte Belegzeile geöffnet hat. Offen
Facts erhält den normalisierten Produkttext, nicht das vollständige Belegbild.
Adress- oder Zahlungsdaten. Der konfigurierte AI-Provider erhält nur die Leitung und
Kandidaten-Metadaten, die für das Ranking benötigt werden. Suchergebnisse werden 30 Tage lang zwischengespeichert.

Referenzen zur Responsive-Implementierung:

- [Kandidaten für mobile Produkte](../design/product-candidates-mobile-final-0.8.0.png)
- [Desktop-Produktkandidaten](../design/product-candidates-desktop-final-0.8.0.png)

Der Produktscanner ist ein separater primärer Arbeitsablauf mit Identifizieren, Hinzufügen,
Konsum-, Öffnungs- und Einkaufslistenmodus. Es unterstützt Telefonkameras über HTTPS,
manuelle Eingabe und Scanner, die sich wie eine Tastatur verhalten. Unbekannte Codes bleiben bestehen
ein Bewertungs-Posteingang statt verloren zu gehen. Siehe [Produktscannen](BARCODE-SCANNING.md).

Bei der manuellen Eingabe werden alle anderen als 4–18 Ziffern mit Leerzeichen und Bindestrichen abgelehnt
nur als Trennzeichen erlaubt, bevor der Server kontaktiert wird. Prüfsumme und Konflikt
Die Validierung wird weiterhin autorisierend auf der API ausgeführt. Strukturierte API-Validierung
Details werden in lesbare Feldnachrichten umgewandelt; Rohobjekte sind niemals
dem Haushalt gezeigt.

## Katalogbearbeitung

1. Öffnen Sie **Vorrat** und wählen Sie ein Produkt aus.
2. Bearbeiten Sie den Haushaltsnamen, das Bild, die Notizen, den Standardstandort, die Einheit und die Produktgruppe
   oder Haltbarkeit. Beim Speichern bleibt der alte Produktname als passender Alias ​​erhalten.
3. Fügen Sie eine konkrete Variante hinzu oder öffnen Sie sie, um Marke, Packungsgröße, Image usw. beizubehalten
   Barcodes. Ein validierter Barcode kann nur zu einer Variante gehören.
4. Eine Variante mit Beleg-, Lager- oder Scan-Referenzen bleibt geschützt. Entfernen bzw
   Korrigieren Sie den Referenzierungsworkflow, anstatt den Verlauf zu löschen.
5. Öffnen Sie **Stammdaten**, um jeden Standort, jede Einheit und jede Gruppe mit ihrem Produkt anzuzeigen
   Nutzungsanzahl. Einträge können sofort hinzugefügt oder umbenannt werden.
6. Das Archiv ist nur verfügbar, wenn kein aktives Produkt den Eintrag mehr verwendet. Die
   Der Herausgeber erklärt, welche Neuzuweisung zuerst erforderlich ist.

Wenn ein anderer Browser denselben Datensatz nach dem Öffnen des Formulars gespeichert hat, wird Vorrio
lehnt die veraltete Speicherung ab und bittet um ein Neuladen, anstatt sie zu überschreiben.

Referenzen zur Responsive-Implementierung:

- [Mobiler Produkteditor](../design/catalog-editor-mobile-final-0.8.1.png)
- [Desktop-Produkteditor](../design/catalog-editor-desktop-final-0.8.1.png)
- [mobiler Stammdateneditor](../design/master-data-editor-mobile-final-0.8.1.png)
- [Desktop-Stammdateneditor](../design/master-data-editor-desktop-final-0.8.1.png)

## Öffnung und Zykluszählung

1. Öffnen Sie **Vorrat → Zählen**. Jedes Mengenfeld beginnt leer; leere Produkte
   liegen außerhalb der Transaktion und bleiben unverändert.
2. Suchen Sie nach Produkt oder Standort und geben Sie die physisch gezählte Menge ein.
   Plus/Minus-Kontrollen beginnen ab dem aktuell erfassten Bestand. Erweitern Sie eine Zeile
   nur wenn Standort, konkrete Variante oder Mindesthaltbarkeitsdatum angepasst werden müssen.
3. Wenn Grocy aktiviert ist, liest **Grocy-Vorschlag** seine aktuellen Salden und
   füllt nur bereits zugeordnete Vorrio-Produkte vor. Nicht zugeordnete positive Grocy-Zeilen
   werden gemeldet und weggelassen. Die Vorschau ändert keine Anwendung.
4. Wählen Sie **Änderungen prüfen**. Vergleichen Sie alle vorherigen und gezählten Mengen;
   Nullunterschiede bleiben sichtbar, erzeugen aber keine Bewegung.
5. Bestätigen Sie einmal. Vorrio erstellt eine unveränderliche Zählsitzung, ihre Zeilen und die
   erforderliche, nur anhängende Lagerbewegungen. Bei Netzwerkwiederholungen wird derselbe Client erneut verwendet
   Mutationsidentifikator und gibt das ursprüngliche Ergebnis zurück.
6. Die Ergebnisberichte eingegebener und geänderter Produkte. Positive Unterschiede entstehen
   viel; Negative Differenzen verbrauchen die am frühesten ablaufenden verfügbaren Chargen
   zuerst.

Der Ablauf eignet sich für eine Erstinventur, ein Regal oder eine spätere Korrektur.
Es handelt sich nicht um eine automatische Grocy-Synchronisierung und es entsteht nie ein Fehler
Produkt- oder Stammdatenerfassung.

Referenzen zur Responsive-Implementierung:

- [Mobile-Count-Eintrag](../design/stock-count-mobile-final-0.8.2.png)
- [Überprüfung der mobilen Zählung](../design/stock-count-review-mobile-final-0.8.2.png)
- [Desktop-Zählereintrag](../design/stock-count-desktop-final-0.8.2.png)
- [Überprüfung der Desktop-Anzahl](../design/stock-count-review-desktop-final-0.8.2.png)

## Mindestbestand und Einkaufsliste

1. Öffnen Sie ein Produkt unter **Vorrat** und setzen Sie **Mindestbestand** plus
   **Auffüllen bis**. Das Ziel muss größer als das Minimum sein; Ziel `0`
   hält die Regel deaktiviert.
2. Öffnen Sie **Einkäufe → Liste**. Eine grüne **Auffüllen**-Karte erscheint nur, wenn eine
   Das berechtigte Produkt ist nicht bereits mit mindestens dem berechneten Wert vertreten
   Mangel.
3. Überprüfen Sie jeden Vorschlag. Vorrio zeigt Strom, Minimum, Ziel und genau an
   vorgeschlagene Menge. Deaktivieren Sie alles, was warten soll.
4. Bestätigen Sie einmal. Der Server überprüft den aktuellen Bestand noch einmal transaktional und überspringt a
   Jetzt wiederhergestelltes Produkt und gibt bei einem erneuten Versuch das ursprüngliche Generierungsergebnis zurück.
5. Ein vorhandener ungeprüfter Artikel wird nur dann erhöht, wenn der neue Mangel größer ist;
   es wird niemals dupliziert oder reduziert. Im Scanner-Einkaufsmodus wird derselbe Artikel verwendet.
6. Passen Sie die Mengen mit Plus/Minus an und haken Sie einen Artikel in der gemeinsamen Liste ab.
   Optimistische Zeitstempel verhindern, dass ein veralteter Browser eine neuere Bearbeitung überschreibt.
7. Wechseln Sie im selben Bildschirm für alle verarbeiteten Belege zu **Bon-Verlauf**.

Die Regel erstellt Vorschläge, keine unbeaufsichtigten Käufe. Der Bestand ändert sich immer noch
stammen aus überprüften Belegen, Paketaktionen oder einer Zählung; einen Artikel abhaken
erfindet keine Aktien.

Referenzen zur Responsive-Implementierung:

- [mobile Einkaufsliste](../design/shopping-list-mobile-final-0.8.3.png)
- [Rezension zum mobilen Nachfüllen](../design/shopping-refill-mobile-final-0.8.3.png)
- [Desktop-Einkaufsliste](../design/shopping-list-desktop-final-0.8.3.png)
- [Rezension zum Auffüllen des Desktops](../design/shopping-refill-desktop-final-0.8.3.png)

## Paketscan

1. Öffnen Sie **Scannen** und wählen Sie die gewünschte Aktion aus, bevor Sie den Code erfassen.
2. Verwenden Sie die HTTPS-Kamera, geben Sie die Ziffern ein oder scannen Sie mit in das fokussierte Feld
   ein USB-, Bluetooth- oder 2,4-GHz-Tastatur-Wedge-Scanner.
3. Wenn der Server nicht verfügbar ist, behält Vorrio nur den Code, die beabsichtigte Aktion usw.
   Zeitstempel und ein stabiler Idempotenzschlüssel in der sichtbaren Warteschlange auf dem Gerät. Es
   trifft offline keine Produkt-, Lager- oder Listenentscheidung.
4. Nach erneuter Verbindung oder **Jetzt abgleichen** validiert Vorrio den Code und prüft zuerst die lokale Variante, dann seine
   externer Cache und Open Facts.
5. Nach der Erkennung wird das Kamerafeld geschlossen und die Überprüfung wird nach oben verschoben.
   Die ausgewählte Aktion und ihre genaue Auswirkung bleiben sichtbar. **Aktionen erklärt**
   öffnet eine Übersicht aller fünf Modi, ohne die aktuelle Auswahl zu ändern.
6. Überprüfen Sie das Produkt und die Quelle. Ordnen Sie ein externes oder unbekanntes Ergebnis einem zu
   bestehendes Produkt, oder bearbeiten Sie den vorgeschlagenen Namen und erstellen Sie ihn bewusst.
7. Fügen Sie Menge, Ort, Datum oder Preis nur dann hinzu, wenn die ausgewählte Aktion erforderlich ist
   Geben Sie diese Werte ein und bestätigen Sie sie einmal.
8. Eine wiederholte Netzwerkanfrage mit demselben Idempotenzschlüssel gibt den ersten zurück
   Ergebnis, anstatt ein weiteres Los oder eine weitere Bewegung zu erstellen.
9. Vorrio vergleicht offene Empfangszeilen erneut mit dem neu bestätigten lokalen Wert
   Barcode und Produkt. Es werden exakte Treffer zugeordnet; Fuzzy-Hits-Aufenthaltsvorschläge.

Durch Hinzufügen entsteht ein neues Los und Bewegung. Verbrauchen entfernt aus dem am frühesten ablaufenden
zuerst die verfügbaren Lose. „Offen“ markiert die früheste geeignete ungeöffnete Charge. Einkaufen
Die Liste verwendet ein vorhandenes ungeprüftes Element für dasselbe Produkt wieder und erhöht dessen Anzahl
gewünschte Menge. Identifizieren Sie Änderungen, keine Lagermenge.

Referenzen zur Responsive-Implementierung:

- [Eintrag für den mobilen Scanner](../design/scanner-entry-mobile-final-0.8.5.png)
- [mobile ergebnisorientierte Überprüfung](../design/scanner-review-mobile-final-0.8.5.png)

## Stammdatenvorschläge

Vorrio vergleicht jeden vorgeschlagenen Standort, jede Einheit und jede Produktgruppe mit der Gesamtheit
lokale Liste. Es wird ein exakter Wert ausgewählt. Ein fehlender Wert bleibt editierbar und muss bearbeitet werden
vor der Erstellung bestätigt werden. Ähnliche, aber semantisch falsche Einträge gibt es nicht
nur gewählt, um die Schaffung eines neuen Wertes zu vermeiden.

## Preise und Belegzeilen

Anzahlungen, Rabatte und andere nicht vorrätige Positionen bleiben außerhalb des Lagerbestands. Die
Die Überprüfung zeigt den Gesamtbetrag des Belegs, den Produktwert und die Differenz. Bestätigtes Produkt
Zeilen speichern Store, Stückpreis, Kaufdatum und eine bekannte Paketvariante für
die Produktpreisverlaufs-API.

Öffnen Sie **Einkäufe → Preise**, um diese bestätigten Beobachtungen zu verwenden. Der Überblick
Gruppiert Filialen nach normalisiertem Einzelhändler, wobei die konkrete Beobachtung beibehalten wird
Ladenetikett und Datum sichtbar. Wenn Sie ein Produkt auswählen, werden die neuesten und niedrigsten Preise angezeigt
Preis, Änderung gegenüber dem vorherigen bestätigten Kauf, aktueller/niedrigster Preis pro Geschäft
Werte und der paketbewusste Verlauf. Entwurf, ungelöst und lediglich vorgeschlagen
Wareneingangszeilen sind ausgeschlossen. Ein Ergebnis beschreibt nur die Haushaltsgeschichte; es ist
kein Live-Preis-, Werbe- oder Verfügbarkeitsanspruch.

## Haushaltsbudget

1. Öffnen Sie **Einkäufe → Budget**. Jede Haushaltsrolle kann die gleiche Übersicht lesen.
2. Eigentümer oder Administrator können **Anpassen** wählen, ein monatliches EUR-Ziel festlegen und auswählen
   der 70-, 80-, 90- oder 100-Prozent-Warnpunkt. Vorrio erfindet nie ein Ziel.
3. Überprüfen Sie den bestätigten Betrag für den laufenden Monat, das verbleibende Ziel und den einfachen Betrag
   Vorhersage im Kalendertempo. Die Prognose extrapoliert vergangene Kalendertage und
   ist eher eine Orientierung als eine Vorhersage.
4. Vergleichen Sie nur das gleiche Fenster mit den verstrichenen Tagen des Vormonats. Sechsmonatsbarren
   und aktuelle Store-Freigaben verwenden dieselbe Zählregel.
5. Überprüfen Sie die Datennotiz, bevor Sie handeln: ein ausstehender Beleg, fehlender Gesamtbetrag oder
   Nicht-EUR-Gesamtsumme bleibt sichtbar, aber ausgeschlossen. Lösen Sie den Beleg wie gewohnt auf
   Überprüfungsworkflow; Die nächste Übersichtsanfrage wird automatisch neu berechnet.
6. Durch das Entfernen eines Ziels bleiben alle Belege und historischen Zusammenfassungen erhalten. Die Aussicht dann
   bleibt als aus Belegen abgeleiteter Ausgabenüberblick nützlich.

Eine Quittung trägt den Betrag erst dann ein, wenn mindestens eine ihrer Zeilen explizit angegeben wurde
der Vorrio-Aktie verpflichtet. Das bloße Hochladen oder Analysieren einer Quittung kann keine Änderung bewirken
das Budget. Die Funktion verbindet weder eine Bank noch beansprucht sie den aktuellen Händler
Preise.

## Doppelte Belege

Identische Dateibytes werden vor einem kostenpflichtigen Provider-Anruf abgelehnt. Ein zweites Foto
oder anders gerenderte PDFs können erst nach der Analyse erkannt werden; Dann Vorrio
Vergleicht Lager, Datum, Gesamtsumme und eine sortierte Signatur von mindestens zwei Produkten
Linien. Bei einer Übereinstimmung wird die vorhandene Bewertung mit `duplicate=true` zurückgegeben und verworfen
der neue temporäre Upload.

## Grocy Übergang

Mit „Katalogübernahme“ kopieren Sie Produkte und Stammdaten sicher in Vorrio.
Der Import ist wiederholbar. Siehe [Grocy-Migration](MIGRATION-GROCY.md).
