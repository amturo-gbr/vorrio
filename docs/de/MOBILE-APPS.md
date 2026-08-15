# iOS- und Android-Apps

## Entscheidung

Die PWA bleibt der schnellste Universal-Client. Die geplanten Store-Apps nutzen
Kondensator 8 um die bestehende React-Anwendung zu starten, anstatt eine zu starten
unabhängige React Native-Umschreibung. Das UI-Bundle ist in jeder App enthalten.
Die App lädt die Vorrio-Website nicht herunter und zeigt sie nicht als Schnittstelle an.

Capacitor behält das gemeinsame TypeScript- und Designsystem bei und ermöglicht gleichzeitig
nativer Swift- und Android-Code, wo die Geräteintegration dies erfordert.

## Nativer Wert

Die erste Store-Version muss mehr als einen Website-Wrapper bieten:

- natives Kamera- und Barcode-Scannen;
- Offline-Scan- und Empfangswarteschlange mit sichtbarem Synchronisierungsstatus;
- Push-Benachrichtigungen mit Deep-Links für niedrige Lagerbestände, abgelaufene Listen und freigegebene Listen;
- Share-Sheet-Import für Quittungsbilder und PDFs;
- Passkeys und Plattform-Anmeldeinformationsmanager;
- sichere Token-Speicherung, biometrische Wiedereingabe und Gerätesitzungsverwaltung;
- Wiederholung des Hintergrund-Uploads innerhalb der Plattformgrenzen;
- Native App-Links und barrierefreie Plattformnavigation.

Diese Funktionen bieten auch den von der App-Store-Überprüfung erwarteten Nutzen.

Für das Scan-Erlebnis gelten dieselben Modi und Auflösungsregeln wie für die PWA:
zuerst lokaler Katalog, optional zwischengespeicherte/externe Anreicherung, explizite Bestätigung
und ein Posteingang mit ungelöstem Code. Siehe [Produktscannen](BARCODE-SCANNING.md).

Die PWA 0.7 implementiert bereits diesen gemeinsamen REST-Vertrag und einen reaktionsfähigen Scan
Oberfläche. Seine Browserkamera verwendet einen gebündelten lokalen Decoder und HTTPS. Einheimisch
Plugins ersetzen später nur die Geräteerfassung; Auflösung, Überprüfung und Bestätigung
Verwenden Sie weiterhin dieselbe versionierte API.

## Anschließen eines selbst gehosteten Servers

Beim ersten Start gibt der Benutzer eine HTTPS-Server-URL ein oder scannt einen Konfigurations-QR
Code. Der QR-Code enthält nur Metadaten der öffentlichen Instanz, niemals ein Passwort,
API-Token oder `APP_SECRET_KEY`.

Ein geplantes `/.well-known/vorrio`-Dokument enthüllt:

- Instanzname und stabile Instanzkennung;
- API und mindestens kompatible Clientversionen;
- kanonische öffentliche URL;
- unterstützte Authentifizierungsmethoden;
- Links für Datenschutz, Support und Metadaten der WebAuthn-Zuordnung.

Release-Builds erfordern ein gültiges HTTPS-Zertifikat. Sie bieten keine an
Schalter „Zertifikatfehler ignorieren“. Es müssen private Zertifizierungsstellen sein
installiert und vom Betriebssystem als vertrauenswürdig eingestuft. Die Browser-PWA folgt demselben Prinzip
Regel für private, kamerafähige HTTPS-Installationen.

## Native Authentifizierung

Das Sitzungscookie desselben Ursprungs des Browsers wird nicht als native API wiederverwendet
Berechtigung. Native Apps verwenden die browserbasierte Autorisierung mit Autorisierung
Code plus PKCE, kurzlebige Zugriffstoken und rotierende, widerrufbare Aktualisierung
Token. Token sind auf eine Instanz, einen Haushalt, einen Benutzer und ein Gerät beschränkt
im sicheren Schlüsselbund oder Android Keystore-gestützten Speicher gespeichert.

CORS mit Wildcard-Anmeldeinformationen ist verboten. Jeder unterstützte App-Ursprung und Link
Die Assoziation ist explizit. iOS Universal Links und Android App Links binden die
installierte App auf dieselbe verifizierte HTTPS-Domäne, die von Passkeys verwendet wird.

Version 0.8.16 bietet separate Haushaltskonten, Rollendurchsetzung,
Passkeys, optionales TOTP, Wiederherstellungscodes und
widerrufbare Browsersitzungen plus bereichsbezogene lokale Automatisierungstoken. Browser
Sitzungen und Automatisierungstoken sind absichtlich keine nativen Aktualisierungstoken; Die
Der zukünftige PKCE-Autorisierungsendpunkt wird einen separaten erstellen
`device_authorization` ist an denselben Benutzer und Haushalt gebunden.

Der eingegebene Server muss Vorrios externes Pfad-Gate bereits erfüllen. Ein Einheimischer
Der Client setzt oder umgeht `PUBLIC_EXPOSURE_ACKNOWLEDGED` nicht, seien Sie vertrauenswürdig
hosts/origins oder greifen Sie auf eine unsichere LAN-URL zurück. Siehe
[Sicherheitsüberprüfung für externen Zugriff](EXTERNAL-ACCESS-SECURITY-REVIEW.md).

## Lieferplan

1. Erweitern Sie die mitgelieferte Basis für Familienkonten/Browsersitzungen mit Native
   Geräteautorisierung und API-Kompatibilitätserkennung.
2. Fügen Sie der REST-API offline-sichere Mutations-IDs und Konfliktantworten hinzu.
3. Erstellen Sie den gemeinsam genutzten Capacitor-Arbeitsbereich und native Scan-/Freigabe-Plugins.
4. Testen Sie iOS über TestFlight und Android über einen internen Play-Track.
5. Fügen Sie Datenschutzmanifeste hinzu, speichern Sie Datenschutzerklärungen, Support und Demomodus.
6. iOS über Amturo UG und Android über Google Play veröffentlichen; bewerten ein
   F-Droid-kompatibler Build nach reproduzierbarer Signatur und Update-Handhabung
   etabliert.
