# Finanzierung Vorrio

Vorrio ist eine Open-Source-Software, die von der Amturo UG verwaltet wird. Die Finanzierung soll unterstützen
Wartung, Sicherheitsarbeiten, Dokumentation, Community-Unterstützung und öffentlicher Bau
Infrastruktur ohne Reduzierung des selbstgehosteten Kerns.

## Geplante erste Option: Stripe Payment Links

Stripe Payment Links ist die bevorzugte Startoption. Die statischen Website-Links
zum von Stripe gehosteten Checkout und lädt weder Stripe-JavaScript noch stellt es eine API bereit
Schlüssel. Dies hält die Website unabhängig von Abhängigkeiten und vermeidet die Kontaktaufnahme mit Stripe
Der Besucher entscheidet sich aktiv für die finanzielle Unterstützung.

Die vorbereitete Website unterstützt zwei unabhängige Links:

- eine einmalige Zahlung, deren Höhe der Unterstützer selbst bestimmt;
- eine optionale feste monatliche Patenschaft.

Beide Steuerelemente bleiben ausgeblendet, während ihre Werte in `website/support-config.js` verborgen bleiben
leer. Informationen zu Konto, Link und Aktivierungsschritten finden Sie unter `STRIPE-SUPPORT.md`.

Zwei Stripe-Links im Testmodus sind vorbereitet: einmalige Unterstützung mit
frei gewähltem Betrag, mindestens 3 EUR und voreingestellt 10 EUR, sowie eine
feste monatliche Unterstützung von 5 EUR. Beide gehosteten Seiten sind
erreichbar, aber kein Testlink wird auf der öffentlichen Website verwendet. Das
idempotente Setup liegt in `scripts/setup_stripe_support.mjs`; lokale Schlüssel,
IDs und Test-URLs bleiben in der von Git ignorierten Datei `.env.stripe.local`.

Die Sandbox-Probe umfasst erfolgreiche einmalige und monatliche Kartenzahlungen,
herunterladbare PDF-Rechnungen, eine abgelehnte Zahlung, das gehostete Kundenportal,
Kündigung des Abonnements am Ende des Zeitraums und vollständige Rückerstattung. Stripe wählt das
Die verfügbaren Zahlungsmethoden werden dynamisch angezeigt, daher muss das Live-Konto überprüft werden
noch einmal vor dem Start, anstatt eine feste öffentliche Methodenliste zu versprechen.

## Aktuellen Status überprüft

Geprüft am 16. August 2026: Das Stripe-Konto kann Zahlungen und Auszahlungen
verarbeiten, hat keine offenen Verifizierungsanforderungen und verwendet EUR.
Öffentliche Support-Kontaktdaten, Vorrio-Branding, Steuer- und
Buchhaltungsfreigaben sowie die Live-Stripe-Objekte fehlen noch. Deshalb bleiben
die Live-Erstellung und alle öffentlichen Zahlungselemente gesperrt.

Ebenfalls überprüft am 13. August 2026: `amturo-gbr/vorrio` ist das kanonische Repository und
ist immer noch privat; Die öffentliche `amturo-gbr`-Organisation stellt derzeit Nr. offen
öffentliche Repositories. Weder `@amturo-gbr` noch `@adrian-amturo` haben sich beworben
Treten Sie GitHub-Sponsoren bei. Es existiert kein `.github/FUNDING.yml`, was beabsichtigt ist
während GitHub Sponsors zurückgestellt wird. Alle Formulierungen und Kontrollen der GitHub-Sponsoren sind
auf der Projektwebsite verborgen.

Belohnungen dürfen Sicherheitskorrekturen nicht verzögern oder wesentliche selbst gehostete Funktionen ermöglichen
exklusiv. Sponsorlogos und öffentliche Namen sind freiwillig.

## Spätere Optionen

Open Collective ist nützlich, wenn die Community ein öffentliches Budget und öffentliche Ausgaben haben möchte
Hauptbuch. Denn die Amturo UG ist bereits eine juristische Person, ein unabhängiges Kollektiv
oder die direkte Buchhaltung kann einfacher sein als ein Fiskal-Host; Buchhaltungsberatung ist
vor der Aktivierung erforderlich.

## Wortlaut und Steuern

Die finanzielle Unterstützung einer gewerblichen UG ist nicht steuerlich absetzbar
Spende, und Vorrio verspricht keine Spendenbescheinigungen. Öffentliche Kopie
verwendet „Unterstützung“ oder „Sponsoring“. Die Amturo UG erfasst Auszahlungen und anfallende Steuern
durch seinen normalen Buchhaltungsprozess.

In 0.8.26 ist kein Live-Zahlungslink öffentlich aktiv. Stripe-Unterstützung ist aktiviert
erst nach Erhalt des Amturo-Kontos, Live-Zahlungslinks, legaler Kopie und
Der Buchhaltungsprozess ist fertig. Geheime Stripe-Schlüssel gehören niemals in `website/` oder
ein Browser-Bundle.

## Website-Aktivierungssequenz

Aufgrund der statischen Projektwebsite ist bis zum Start keine finanzielle Unterstützung verfügbar
Tore sind fertig:

1. Vervollständigen und überprüfen Sie das Amturo Stripe-Geschäftskonto, das Auszahlungskonto und
   Steuerdetails;
2. den Wortlaut des öffentlichen Sponsorings, die Mehrwertsteuerbehandlung und den Buchhaltungsablauf genehmigen;
3. Erstellen Sie im Testmodus die einmaligen und optionalen monatlichen Stripe Payment Links
   (**vorbereitet**);
4. Überprüfen Sie den Checkout, PDF-Rechnungen, eine fehlgeschlagene Zahlung, das Kundenportal,
   Rückerstattungen und Abonnementkündigung (**im Testmodus überprüft**);
5. Erstellen Sie die Live-Links und fügen Sie nur deren öffentliche `buy.stripe.com`-URLs hinzu
   `website/support-config.js`;
6. Überprüfen Sie beide Sprachen und Zahlungsflüsse in einem abgemeldeten Browser.

PayPal ist nicht die Standardeinstellung beim Start. Ein eigenständiger PayPal-Button würde einen weiteren hinzufügen
Checkout, Abgleich und Legal-Copy-Pfad ohne Verbesserung der Quelle-zu-Kopie
Support-Flow, der bereits von Stripe bereitgestellt wird. Es kann später noch einmal überdacht werden
nur, wenn die Unterstützer es nachweislich benötigen und Amturo dem Geschäft zugestimmt hat
Konto, Gebühren, Rückerstattungen, Datenschutzbestimmungen und buchhalterische Behandlung. Offen
Kollektiv bleibt eine spätere Transparenzoption, wenn Vorrio eine Community aufbaut
Budget, das über ein öffentliches Einnahmen- und Ausgabenbuch verfügt.
