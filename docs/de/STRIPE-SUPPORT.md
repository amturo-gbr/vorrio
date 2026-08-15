# Stripe-Unterstützungsintegration

Vorrio nutzt für die finanzielle Unterstützung von Stripe gehostete Zahlungslinks. Das ist das
kleinste Integration, die eine statische Website unterstützt: Zahlungsdaten bleiben bestehen
Stripe Checkout, die Vorrio-Website lädt kein Stripe-JavaScript und kein Geheimnis oder
Im Browser ist ein veröffentlichbarer API-Schlüssel erforderlich.

## Grenze der öffentlichen Website

Die öffentliche Vercel-Bereitstellung enthält keine Stripe-Steuerelemente, Stripe-Kopie oder Stripe
Laufzeitcode. `website/.vercelignore` schließt den lokalen Platzhalter aus
`website/support-config.js`, dessen zwei leere URL-Slots für später reserviert sind
Aktivierungsänderung:

```js
window.VORRIO_SUPPORT_LINKS = Object.freeze({
  oneTime: '',
  monthly: '',
})
```

Der Platzhalter wird nicht von öffentlichem HTML oder JavaScript referenziert. Aktivierend
Zahlungen erfordern eine überprüfte Änderung, die die Live-Kontrollen und strengen Kontrollen hinzufügt
`https://buy.stripe.com/` URL-Validierung, entfernt den Vercel-Ausschluss, aktualisiert
die Datenschutzerklärung und verifiziert beide Sprachen. Testlinks dürfen niemals kopiert werden
in öffentliche Website-Dateien.

Geben Sie hier niemals `sk_test_`, `sk_live_`, eingeschränkte Schlüssel oder Webhook-Geheimnisse ein
Datei, eine andere Datei unter `website/`, Git, Screenshots oder Browsercode.

## Aktueller Teststatus

Erstellt am 13. August 2026:

- `scripts/setup_stripe_test_support.mjs` erstellt oder verwendet idempotently das
  zwei Produkte im Testmodus, Preise und Zahlungslinks über die API von Stripe;
- Der einmalige Testpreis akzeptiert einen vom Kunden gewählten EUR-Betrag mit a
  Mindestens 3 EUR und voreingestellt 10 EUR;
- Der wiederkehrende Testpreis ist auf 5 EUR pro Monat festgelegt.
- Beide von Stripe gehosteten Testlinks sind aktiv und geben HTTP 200 zurück;
- Der einmalige Link erstellt eine bezahlte Stripe-Rechnung mit herunterladbarem PDF;
- Der monatliche Link erstellt ein Abonnement und die erste bezahlte Rechnung;
- Das gehostete Kundenportal zeigt den Rechnungsverlauf, Rechnungsdetails und Zahlungsinformationen an.
  Methodenaktualisierungen und Stornierung am Ende des Abrechnungszeitraums;
- Ihre Test-IDs und URLs werden lokal unter `.env.stripe.local` gespeichert
  wird von Git ignoriert und muss privat bleiben;
- `website/support-config.js` bleibt leer und wird von Vercel ausgeschlossen, also testen
  Links und inaktive Zahlungsformulierungen dürfen nicht auf der öffentlichen Website erscheinen.

Das Setup-Skript akzeptiert nur einen eingeschränkten `rk_test_`-Schlüssel und lehnt die Live-Version ab
Modus. Bei einer erneuten Ausführung müssen die vorhandenen Objekte zurückgegeben und nicht erstellt werden
Duplikate.

Die komplette Sandbox-Probe fand ebenfalls am 13. August 2026 statt:

- Eine einmalige Kartenzahlung in Höhe von 10 EUR wurde erfolgreich abgeschlossen.
- ein erfolgreich abgeschlossenes Kartenabonnement im Wert von 5 EUR pro Monat;
- Stripe erstellte herunterladbare PDF-Rechnungen für beide erfolgreichen Abläufe;
- eine abgelehnte Testkarte blieb erfolglos und führte zu keiner bezahlten Transaktion;
- Das Monatsabonnement wurde im gehosteten Portal gekündigt und endet nun um
  das Ende des aktuellen Abrechnungszeitraums;
- Die Einmalzahlung wurde vollständig zurückerstattet und wird im Konto als zurückerstattet ausgewiesen
  Streifen-Dashboard.

An der Kasse wurde die dynamische Zahlungsmethodenauswahl von Stripe angezeigt und nicht eine
hartcodierte Liste. Die genauen Methoden variieren je nach Unterstützer, Browser, Gerät und Währung
und Stripe-Kontoberechtigung und muss daher im Live-Modus erneut überprüft werden.

## Empfohlene Einrichtung eines Stripe-Kontos

Nutzen Sie die Geschäftsidentität und Geschäftsauszahlung der Amturo UG (haftungsbeschränkt).
Konto. Überprüfen Sie vor dem Erstellen von Live-Links Folgendes:

- Firmenname, Adresse, Register und wirtschaftliche Eigentümer;
- Bankkonto und Steuerdaten für die Auszahlung;
- öffentliche Support-E-Mail-Adressen und Website-Datenschutz-/Impressum-URLs;
– Anweisungsdeskriptor, der Amturo oder Vorrio eindeutig identifiziert;
- Branding mit dem Vorrio-Logo und `#176B35` Akzentfarbe;
- automatische Belege, Rückerstattungsabwicklung und relevante Zahlungsmethoden;
- Stripe-Datenverarbeitungsbedingungen und der interne Buchhaltungsworkflow.

Die endgültige steuerliche und umsatzsteuerliche Behandlung gewerblicher Sponsoringeinnahmen muss vereinbart werden
vor der Aktivierung mit dem Steuerberater von Amturo. Öffentliche Formulierungen verwenden „Unterstützung“ oder
„Sponsoring“, keine Zusage einer steuerlich absetzbaren Spende oder Spendenquittung.

## Vorbereitete Zahlungslinks

### 1. Einmalige Unterstützung

- Typ: **Kunden entscheiden, was sie bezahlen möchten**.
- Titel: `Vorrio einmalig unterstützen`.
- Empfohlener Betrag: 10 EUR.
- Empfohlener Mindestbetrag: 3 EUR.
- Aufruf zum Handeln: Zahlungs-/Unterstützungsformulierung, kein Versprechen einer wohltätigen Spende.
- Sammeln Sie nur die Informationen, die für Zahlungen, Quittungen und Buchhaltung erforderlich sind.

Dieses Stripe-Preismodell ist nur einmalig; Es können keine wiederkehrenden Zahlungen erstellt werden.

### 2. Optionaler monatlicher Support

- Typ: **Produkt oder Abonnement**.
- Produkt: `Vorrio monatlich unterstützen`.
- Erster Festpreis: 5 EUR pro Monat.
- Bereitstellung der Stornierungs- und Zahlungsmethodenverwaltung über Stripe
  gehostetes Kundenportal oder die Stripe-Kunden-E-Mails.
- Versprechen Sie keine Produktkontrollrechte, exklusive Sicherheitsupdates oder wesentliche Verbesserungen
  selbstgehostete Funktionalität als Belohnung.

Weitere monatliche Stufen können später hinzugefügt werden, wenn die tatsächliche Nachfrage dies rechtfertigt
Kopier- und Buchhaltungskomplexität.

## Test- und Aktivierungssequenz

1. Erstellen Sie beide Links im Stripe-Testmodus. **Vorbereitet.**
2. Lassen Sie `website/support-config.js` während des Tests leer und von Vercel ausgeschlossen
   die Links direkt. **Verifiziert.**
3. Testen Sie erfolgreiche einmalige und monatliche Zahlungen, eine fehlgeschlagene Zahlung, PDF
   Rechnungen, Zugang zum Kundenportal, wiederkehrende Stornierung und Rückerstattung.
   **Im Stripe-Testmodus überprüft.**
4. Bestätigen Sie den Datenschutztext, die Bedingungen und den Abrechnungsprozess.
5. Erstellen oder aktivieren Sie die Live-Zahlungslinks.
6. Fügen Sie nur die beiden Live-URLs `https://buy.stripe.com/...` zusammen mit „guarded“ hinzu
   öffentliche Kontrollen und die entsprechende deutsche und englische Datenschutzerklärung.
7. Entfernen Sie `support-config.js` nur in der überprüften Änderung aus `.vercelignore`.
8. Führen Sie `make website-check` aus und überprüfen Sie die deutschen und englischen Seiten.
9. Testen Sie die öffentlichen Links vor dem Start in einem abgemeldeten Browser.

Die öffentliche Website benötigt bewusst keine Stripe-API-Integration. Lokale API
Die Automatisierung wird nur für die wiederholbare Einrichtung eines Stripe-Kontos verwendet. Besucher nutzen es immer noch
Von Stripe gehostete Zahlungslinks. Wenn Vorrio schließlich bezahlte Leistungen gewährt oder benötigt
Berechtigungsstatus, ersetzen Sie diesen Ansatz durch vom Server erstellte Checkout-Sitzungen
plus signaturverifizierte Webhooks.
