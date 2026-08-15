# KI-Anbieter und -Modelle

Das Backend unterstützt OpenAI-kompatible Chat Completions APIs von Anthropic
Nachrichten-API und lokale OpenAI-kompatible Endpunkte wie Ollama. Die Auserwählten
Der Anbieter erhält die gerenderten Belegseiten und bei digitalen PDFs lokal
extrahierter Text. Geheimnisse bleiben im Backend.

Fehlerkörper von Remote-Anbietern bleiben ebenfalls an dieser Grenze. Nur Vorrio zeigt
die HTTP-Statuskategorie und einen kurzen Hinweis zu Anmeldeinformationen, Endpunkt,
Ratenlimit oder Serviceverfügbarkeit; Es handelt sich um willkürliche Antwortinhalte Dritter
nie in der PWA gerendert.

## OpenAI-Voreinstellungen

Der Einstellungsbildschirm behält das aktuelle Modell bei, bis der Benutzer es explizit ändert
es und bietet diese Voreinstellungen:

- `gpt-5.4-mini`: empfohlenes Gleichgewicht für Quittungssicht und strukturiertes JSON;
- `gpt-5-mini`: wirtschaftlich etablierte Alternative;
- `gpt-5.6-luna`: kostengünstige Option für die neueste Familie;
- `gpt-5.6-terra`: Option mit höherer Qualität, wenn die Kosten zweitrangig sind;
- Benutzerdefinierte Modell-ID: hält Experimente und zukünftige Modelle möglich.

Alle Anbieter müssen die Bildeingabe unterstützen. Ein günstigeres Nur-Text-Modell reicht nicht aus
für fotografierte Belege. Lokale Modelle halten Bilder im Haushaltsnetzwerk,
Genauigkeit und benötigter RAM/GPU hängen jedoch stark vom gewählten Vision-Modell ab.

Durch die Änderung eines Modells werden keine Katalog- oder Bestandsdaten geändert. Es betrifft nur die Zukunft
Analysen; Überprüfungs- und Bestätigungsregeln sind anbieterunabhängig.

## Produktkandidaten-Ranking

Wenn ein Haushaltsmitglied explizit eine nicht aufgelöste Belegzeile öffnet, kann Vorrio dies tun
Fragen Sie Open Facts nach echten Produktdatensätzen. Der ausgewählte KI-Anbieter empfängt nur
die normalisierte Linie, Händler-/Ladenetikett, bekannte Marke, Menge, Quittung
Stückpreis und eine reduzierte Liste der zurückgegebenen Kandidatenmetadaten. Das ist nicht der Fall
Kandidatenbilder oder den kompletten Beleg noch einmal erhalten.

Das Modell darf nur Bezeichner aus dieser bereitgestellten Liste plus Konfidenz zurückgeben
und ein kurzer Grund. Vorrio kombiniert dies mit deterministischem Namen, Marke,
Paket- und Händlernachweise. Das Scheitern des Anbieters lässt die echten Kandidaten außen vor
ihre deterministische Ordnung. Das Modell kann niemals erstellen oder automatisch zuweisen
ein Produkt, Barcode, Bild oder Preis. Wenn Open Facts passende Bilder liefert,
Bei der abschließenden Drei-Karten-Überprüfung bleiben bis zu zwei bildgestützte Datensätze erhalten, selbst wenn
Die optionale KI-Reihenfolge würde sonst alle verbergen.

Bei digitalen PDFs ist auch die eingebettete Textreihenfolge Teil der Extraktion
Vertrag: Eine Mengen- oder Einheitspreisfortsetzungszeile gehört nur zum
unmittelbar vorangehendes Druckprodukt. Mehrdeutige Fortsetzungszeilen müssen bestehen bleiben
nicht zugewiesen, sondern auf ein anderes Element verschoben.
