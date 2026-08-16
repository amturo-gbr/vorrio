# Finanzierung von Vorrio

Vorrio ist freie Software und wird von der Amturo UG gepflegt. Finanzielle
Unterstützung soll Wartung, Sicherheitsarbeit, Dokumentation,
Community-Unterstützung und öffentliche Build-Infrastruktur finanzieren, ohne
den selbst gehosteten Kern einzuschränken.

## Erste Option: Stripe Payment Links

Stripe Payment Links ist die bevorzugte Lösung zum Start. Die statische Website
verweist auf den von Stripe gehosteten Checkout und lädt weder Stripe-JavaScript
noch API-Schlüssel. Dadurch bleibt die Website unabhängig und kontaktiert
Stripe erst, nachdem sich ein Besucher aktiv für finanzielle Unterstützung
entschieden hat.

Die Website verwendet vier getrennte Live-Links:

- eine einmalige Zahlung mit frei wählbarem Betrag;
- feste monatliche Unterstützung über 5 EUR, 10 EUR oder 25 EUR.

Die öffentlichen URLs stehen in `website/support-config.js`; dort befinden sich
keine API-Schlüssel. Konto-, Link- und Betriebsdetails stehen in
`STRIPE-SUPPORT.md`.

Vier Stripe-Testlinks sind vorbereitet: eine frei wählbare Einmalzahlung ab
2 EUR mit einem Vorschlagsbetrag von 10 EUR sowie monatliche Unterstützung über
5 EUR, 10 EUR oder 25 EUR. Alle gehosteten Seiten sind erreichbar, aber kein
Testlink steht auf der öffentlichen Website. Das idempotente Setup befindet
sich in `scripts/setup_stripe_support.mjs`; lokale Schlüssel, IDs und Test-URLs
bleiben in der von Git ignorierten `.env.stripe.local`.

Der Sandbox-Durchlauf umfasst erfolgreiche einmalige und monatliche
Kartenzahlungen, herunterladbare PDF-Rechnungen, eine abgelehnte Zahlung, das
gehostete Kundenportal, eine Kündigung zum Ende des Abrechnungszeitraums und
eine vollständige Erstattung. Stripe wählt die angebotenen Zahlungsmethoden
dynamisch. Deshalb muss das Live-Konto vor dem Start erneut kontrolliert werden,
statt öffentlich eine feste Methodenliste zu versprechen.

## Bestätigter aktueller Stand

Geprüft am 16. August 2026: Das Stripe-Konto kann Zahlungen und Auszahlungen
verarbeiten, hat keine offenen Verifizierungsanforderungen und verwendet EUR.
Der öffentliche Supportkontakt, das gemeinsame Amturo-Checkout-Branding,
automatische Belege, tägliche Auszahlungen, vier Live-Payment-Links und das
Kundenportal sind eingerichtet. Vorrio ist die Identität der einzelnen Produkte
und Payment Links und ersetzt nicht die globale Identität des Amturo-Kontos.
Da keine aktive Stripe-Tax-Registrierung besteht, bleibt `automatic_tax` aus.

Ebenfalls geprüft am 13. August 2026: `amturo-gbr/vorrio` ist das kanonische
Repository und weiterhin privat; die öffentliche Organisation `amturo-gbr`
enthält derzeit keine öffentlichen Repositories. Weder `@amturo-gbr` noch
`@adrian-amturo` hat GitHub Sponsors beantragt. Eine `.github/FUNDING.yml`
existiert daher bewusst noch nicht. Sämtliche GitHub-Sponsors-Texte und
Schaltflächen sind auf der Projektwebsite verborgen.

Gegenleistungen dürfen Sicherheitskorrekturen nicht verzögern und keine
wesentlichen Self-Hosting-Funktionen exklusiv machen. Sponsorlogos und
öffentliche Namensnennung sind freiwillig.

## Spätere Optionen

Open Collective kann sinnvoll werden, wenn die Community ein öffentliches
Budget und Ausgabenregister wünscht. Da die Amturo UG bereits eine juristische
Person ist, kann eine eigene Abrechnung einfacher als ein Fiscal Host sein;
hierzu ist vor der Aktivierung eine buchhalterische Beratung erforderlich.

## Formulierung und Steuern

Finanzielle Unterstützung einer gewerblichen UG wird nicht als steuerlich
absetzbare Spende dargestellt, und Vorrio verspricht keine
Spendenbescheinigungen. Öffentlich werden „Unterstützung“ oder „Sponsoring“
verwendet. Die Amturo UG verbucht Auszahlungen und gegebenenfalls anfallende
Steuern in ihrem regulären Buchhaltungsprozess.

Die Live-Payment-Links werden ab dem 16. August 2026 öffentlich verwendet.
Geheime Stripe-Schlüssel gehören niemals in `website/` oder ein Browser-Bundle.

## Aktivierungsreihenfolge für die Website

Die statische Projektwebsite lässt finanzielle Unterstützung deaktiviert, bis
alle Startbedingungen erfüllt sind:

1. Amturo-Stripe-Geschäftskonto, Auszahlungskonto und Steuerdaten vollständig
   prüfen;
2. öffentliche Sponsoring-Texte, Umsatzsteuerbehandlung und Buchungsablauf
   freigeben;
3. den einmaligen und die drei monatlichen Stripe-Payment-Links im Testmodus
   anlegen (**vorbereitet**);
4. Checkout, PDF-Rechnungen, fehlgeschlagene Zahlung, Kundenportal,
   Erstattungen und Abo-Kündigung prüfen (**im Testmodus bestätigt**);
5. die Live-Links erzeugen und ausschließlich deren öffentliche
   `buy.stripe.com`-URLs in `website/support-config.js` eintragen;
6. beide Sprachen und Zahlungsabläufe in einem abgemeldeten Browser prüfen.

PayPal ist zum Start keine separate Standardoption. Eine zusätzliche
PayPal-Schaltfläche würde einen weiteren Checkout-, Abstimmungs- und
Rechtstextpfad schaffen, ohne den bereits über Stripe angebotenen Ablauf zu
verbessern. PayPal kann später erneut bewertet werden, wenn Unterstützer es
nachweislich benötigen und Amturo Geschäftskonto, Gebühren, Erstattungen,
Datenschutztexte und buchhalterische Behandlung freigegeben hat. Open Collective
bleibt eine spätere Transparenzoption, falls Vorrio ein Community-Budget mit
öffentlichem Einnahmen- und Ausgabenregister entwickelt.
