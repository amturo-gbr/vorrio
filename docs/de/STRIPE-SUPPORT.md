# Stripe-Unterstützung

Vorrio nutzt von Stripe gehostete Payment Links für finanzielle Unterstützung.
Dies ist die kleinste sinnvolle Integration für eine statische Website:
Zahlungsdaten verbleiben bei Stripe Checkout, die Vorrio-Website lädt kein
Stripe-JavaScript und benötigt im Browser weder einen geheimen noch einen
veröffentlichbaren API-Schlüssel.

## Grenze der öffentlichen Website

Die öffentliche Vercel-Bereitstellung enthält fünf öffentliche Stripe-Ziele:
vier gehostete Checkout-Seiten und das gehostete Kundenportal. Die statische
Website lädt weiterhin kein Stripe-Skript. `website/support-config.js` enthält
nur öffentliche URLs und wird zusammen mit der Website ausgeliefert:

```js
window.VORRIO_SUPPORT_LINKS = Object.freeze({
  oneTime: 'https://buy.stripe.com/...',
  monthly5: 'https://buy.stripe.com/...',
  monthly10: 'https://buy.stripe.com/...',
  monthly25: 'https://buy.stripe.com/...',
  portal: 'https://billing.stripe.com/p/login/...',
})
```

`support.js` akzeptiert ausschließlich HTTPS-Links der Hosts `buy.stripe.com`
und `billing.stripe.com`; ungültige Ziele werden ausgeblendet. Testlinks dürfen
niemals in öffentliche Website-Dateien kopiert werden.

`sk_test_`, `sk_live_`, eingeschränkte Schlüssel oder Webhook-Geheimnisse dürfen
niemals in dieser Datei, anderen Dateien unter `website/`, Git, Screenshots oder
Browsercode erscheinen.

## Aktueller Teststatus

Am 16. August 2026 erneut gegen Stripe API `2026-06-24.dahlia` geprüft:

- `scripts/setup_stripe_support.mjs` erstellt oder verwendet die Testprodukte,
  vier Preise und vier Payment Links idempotent über die Stripe-API;
- der einmalige Testpreis erlaubt einen frei gewählten Eurobetrag ab 2 EUR und
  schlägt 10 EUR vor;
- die drei wiederkehrenden Testpreise betragen 5 EUR, 10 EUR und 25 EUR pro
  Monat;
- alle vier von Stripe gehosteten Testlinks sind aktiv und liefern HTTP 200;
- der einmalige Link kann eine bezahlte Stripe-Rechnung mit herunterladbarer PDF
  erzeugen;
- die monatlichen Links erzeugen ein Abonnement und die erste bezahlte Rechnung;
- das gehostete Kundenportal bietet Rechnungsverlauf, Rechnungsdaten,
  Zahlungsmitteländerung und Kündigung zum Ende des Abrechnungszeitraums;
- Test-IDs und Test-URLs liegen ausschließlich in der von Git ignorierten
  `.env.stripe.local` und müssen privat bleiben;
- Testlinks bleiben vollständig von den öffentlichen Live-URLs getrennt.

Das Setup-Skript verwendet standardmäßig den Testmodus und akzeptiert dort nur
einen eingeschränkten `rk_test_`-Schlüssel. Eine erneute Ausführung verwendet
vorhandene Objekte, statt Duplikate anzulegen. Eine separate, nur lesende
Integrationsprüfung kontrolliert die Stripe-Sandbox, ohne Zugangsdaten
auszugeben:

```bash
node scripts/check_stripe_test_support.mjs
```

Der vollständige Sandbox-Durchlauf wurde am 13. August 2026 außerdem mit den
ursprünglichen Links für einmalig mindestens 3 EUR und monatlich 5 EUR geprüft:

- Eine einmalige Kartenzahlung über 10 EUR war erfolgreich.
- Ein monatliches Kartenabonnement über 5 EUR war erfolgreich.
- Stripe erzeugte für beide erfolgreichen Abläufe herunterladbare
  PDF-Rechnungen.
- Eine abgelehnte Testkarte blieb ohne bezahlte Transaktion.
- Das Monatsabonnement wurde im Portal gekündigt und endet zum Ablauf des
  aktuellen Abrechnungszeitraums.
- Die Einmalzahlung wurde vollständig erstattet und im Stripe-Dashboard als
  erstattet ausgewiesen.

Checkout verwendete Stripes dynamische Zahlungsmittelauswahl und keine
hartcodierte Liste. Die tatsächlich angebotenen Methoden hängen von
unterstützender Person, Browser, Gerät, Währung und Stripe-Berechtigung ab und
müssen daher im Live-Modus erneut kontrolliert werden.

Am 16. August 2026 wurden die überarbeiteten Seiten erneut über die API sowie in
Desktop- und Mobilbrowsern geprüft. Stripe lehnte 1 EUR mit dem erwarteten
Hinweis auf den Mindestbetrag von 2 EUR ab, zeigte den Vorschlagswert von 10 EUR
und stellte die Monatsstufen 5 EUR, 10 EUR und 25 EUR korrekt dar. Es wurde keine
reale Zahlung ausgeführt.

## Prüfung des Live-Kontos

Das empfangende Stripe-Konto wurde am 16. August 2026 geprüft. Die
Unternehmensdaten sind eingereicht, Zahlungen und Auszahlungen sind aktiviert,
EUR ist die Standardwährung, es bestehen keine offenen
Verifizierungsanforderungen und die Zahlungsbeschreibung weist Amturo aus. Die
zwei Live-Produkte, vier Live-Preise, vier Payment Links und das gehostete
Kundenportal sind angelegt. Amturo-Branding, Supportadresse, automatische
Zahlungsbelege und tägliche Auszahlungen sind kontoweit eingerichtet.

Öffentliche Support-E-Mail, Amturo-Support-URL, Amturo-Website und
Amturo-Datenschutz-URL sind im gemeinsamen Konto eingetragen.

Das Konto enthält derzeit keine aktive Stripe-Tax-Registrierung;
`automatic_tax` bleibt daher bewusst aus. Stripe legt die steuerliche und
umsatzsteuerliche Einordnung nicht fest; sie muss im Jahresabschluss der Amturo
UG korrekt behandelt werden.

Für Live sollte ein separater eingeschränkter Schlüssel angelegt werden: mit
Lesezugriff auf grundlegende Konto- und Kontaktinformationen sowie
Schreibzugriff ausschließlich auf Produkte, Preise, Payment Links und das
Kundenportal. Test- und Live-Schlüssel bleiben getrennt. Die private lokale
Vorlage wird außerhalb von Git ausgefüllt und zunächst nur lesend geprüft:

```bash
cp .env.stripe.live.example .env.stripe.live.local
node scripts/setup_stripe_support.mjs --live
```

Ohne `--apply` prüft der Live-Modus lediglich Konto und Freigaben und erstellt
nichts. Auch `--live --apply` ist geschützt und verweigert Schreibvorgänge,
solange ein Pflichtfeld oder eine Freigabe fehlt. Erzeugte Live-IDs und URLs
bleiben ausschließlich in `.env.stripe.live.local`; die öffentliche Website
wird vom Skript nicht verändert.

## Empfohlene Stripe-Kontoeinstellungen

Als Zahlungsempfänger dienen die Unternehmensidentität und das Auszahlungskonto
der Amturo UG (haftungsbeschränkt). Vor der Erstellung von Live-Links sind zu
prüfen:

- rechtlicher Name, Anschrift, Register und wirtschaftlich Berechtigte;
- Auszahlungskonto und Steuerdaten;
- öffentliche Support-E-Mail sowie Datenschutz- und Impressums-URLs;
- eine Zahlungsbeschreibung, die Amturo eindeutig ausweist;
- kontoweites Amturo-Branding; Vorrio bleibt die Identität des jeweiligen
  Produkts und Payment Links;
- automatische Belege, Erstattungsablauf und relevante Zahlungsmethoden;
- Stripe-Datenverarbeitungsbedingungen und interner Buchungsablauf.

Die endgültige steuerliche und umsatzsteuerliche Einordnung gewerblicher
Unterstützung muss vor der Aktivierung mit der Steuerberatung von Amturo
abgestimmt werden. Öffentlich wird von „Unterstützung“ oder „Sponsoring“
gesprochen, nicht von einer steuerlich absetzbaren Spende oder einer
Spendenbescheinigung.

## Vorbereitete Payment Links

### 1. Einmalige Unterstützung

- Typ: **Kundinnen und Kunden wählen den Betrag**.
- Titel: `Vorrio einmalig unterstützen`.
- Vorgeschlagener Betrag: 10 EUR.
- Mindestbetrag: 2 EUR.
- Handlungsaufforderung: Zahlung/Unterstützung, kein Versprechen einer
  gemeinnützigen Spende.
- Es werden nur Daten erfasst, die für Zahlung, Beleg und Buchhaltung nötig
  sind.

Dieses Stripe-Preismodell ist ausschließlich einmalig und kann keine
wiederkehrenden Zahlungen erzeugen.

### 2. Optionale monatliche Unterstützung

- Typ: **Produkt oder Abonnement**.
- Produkt: `Vorrio monatlich unterstützen`.
- Feste Stufen: 5 EUR, 10 EUR und 25 EUR pro Monat.
- Kündigung und Zahlungsmittelverwaltung erfolgen über das gehostete
  Stripe-Kundenportal oder die Stripe-Kunden-E-Mails.
- Es werden keine Mitbestimmungsrechte, exklusiven Sicherheitskorrekturen oder
  wesentlichen Self-Hosting-Funktionen als Gegenleistung versprochen.

Jede Stufe besitzt einen eigenen Payment Link und verwendet dasselbe gehostete
Kundenportal.

## Test- und Aktivierungsreihenfolge

1. Alle vier Links im Stripe-Testmodus erstellen. **Erledigt.**
2. Testlinks von der öffentlichen Live-Konfiguration trennen. **Erledigt.**
3. Erfolgreiche einmalige und monatliche Zahlungen, eine fehlgeschlagene
   Zahlung, PDF-Rechnungen, Kundenportal, Abo-Kündigung und Erstattung testen.
   **Im Stripe-Testmodus bestätigt.**
4. Gemeinsames Amturo-Checkout-Branding prüfen. **Erledigt.**
5. Deutsche und englische Datenschutzhinweise ergänzen. **Erledigt.**
6. Live-Produkte, -Preise, Payment Links und Kundenportal anlegen. **Erledigt.**
7. Nur öffentliche Live-URLs mit geschützten Schaltflächen veröffentlichen.
   **Erledigt.**
8. `support-config.js` aus `.vercelignore` entfernen. **Erledigt.**
9. `make website-check` ausführen und die deutschen und englischen Seiten
   prüfen.
10. Vor dem Start alle öffentlichen Links in einem abgemeldeten Browser testen.

Die öffentliche Website benötigt bewusst keine Stripe-API-Integration. Lokale
API-Automatisierung dient nur der wiederholbaren Einrichtung des Stripe-Kontos;
Besucher verwenden weiterhin von Stripe gehostete Payment Links. Wenn Vorrio
später bezahlte Leistungen oder Berechtigungsstatus benötigt, muss dieser Ansatz
durch serverseitig erzeugte Checkout Sessions und signaturgeprüfte Webhooks
ersetzt werden.
