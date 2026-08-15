# Bereitstellungsprofile und URLs

Der Webclient von Vorrio verwendet relative `/api/v1`-URLs. Der Browser spricht also
zum gleichen Ursprung, der der PWA diente. Version 0.8.16 erfordert keine Hardcodierung
externe URL, der Wechsel von einem LAN-Hostnamen zu einem HTTPS-Hostnamen jedoch nicht
erfordern einen Neuaufbau des Frontends.

Version 0.8.16 erzwingt vertrauenswürdige Hosts, eingeschränkte weitergeleitete Header und Herkunft
Überprüfungen, Anmeldedrosselung, Ressourcenlimits, lokale Familienkonten, Hash
serverseitige Browsersitzungen, REST-Rollenberechtigungen, Passkeys, optionales TOTP,
Einmal-Wiederherstellungscodes, aktuelle Authentifizierung, datenschutzsichere Vorgänge,
tragbarer Export/Löschung und eine vorbereitete signierte Release-Pipeline. Direktes Internet
Die Gefährdung ist bis zur Verabschiedung des geprüften öffentlichen Auftrags und des Betreibers gesperrt
nimmt dies ausdrücklich zur Kenntnis. LAN- und Private-VPN/HTTPS-Profile werden weiterhin unterstützt.

## Unterstützte Zugriffsprofile

| Profil | Empfohlene Adresse | Cookie-Modus | Notizen |
|---|---|---|---|
| Nur LAN | `http://vorrio.lan:9380` | nicht sicher | Einfaches Bewertungsprofil; Manuelle/Hardware-Scans funktionieren, aber die Browser-Kamera-Erfassung erfordert HTTPS. |
| Privates VPN | `https://vorrio.example.com` | Sicher | Bevorzugtes Fernzugriffsprofil, wenn nur Haushaltsgeräte Zugriff benötigen. |
| Öffentliches HTTPS | `https://vorrio.example.com` | Sicher | Erfordert die vollständige Internet-Sicherheitsschleuse. |
| LAN und Remote | derselbe HTTPS-Hostname innen und außen | Sicher | Empfohlen durch Split-DNS, Hairpin-Routing oder einen Tunnel. |

Durch die Verwendung eines kanonischen HTTPS-Hostnamens werden zwei unabhängige Cookie-Kontexte vermieden und
ist für eine vorhersehbare Passkey-Relying-Party-Identität erforderlich. Eine rohe IP-Adresse
sollte nicht zur dauerhaften Identität einer Installation werden.

Direktes LAN-HTTP und öffentliches HTTPS können an denselben Container weitergeleitet werden, jedoch an diesen
ist nicht das empfohlene authentifizierte Setup. Mit `SESSION_HTTPS_ONLY=true`, a
Der Browser sendet sein Sitzungscookie absichtlich nicht über HTTP. Stellen Sie es ein
`false` allein zur Beibehaltung des HTTP-Zugriffs schwächt die öffentliche Installation.

Für einen privaten Kameratest wird eine interne Zertifizierungsstelle benötigt, die von einem gepflegten Reverse-Proxy ausgestellt wird
ist akzeptabel, nachdem jedes teilnehmende Gerät dieser Zertifizierungsstelle ausdrücklich vertraut. Verwenden
einen Hostnamen anstelle eines Roh-IP-Zertifikats, sodass TLS-Clients eine vorhersehbare Nachricht senden
Servername. Native Store-Clients bieten keine Option zum Ignorieren einer
nicht vertrauenswürdiges Zertifikat.

## Bereitstellungsvariablen

| Variable | Zweck |
|---|---|
| `PUBLIC_URL` | Optionale kanonische HTTPS-URL für absolute Links, Passkeys, OAuth-Rückrufe und Push-Metadaten. Es entscheidet nicht, welche Hosts akzeptiert werden. |
| `TRUSTED_HOSTS` | Durch Kommas getrennte Hostnamen, die im HTTP-Header `Host` akzeptiert werden. Jedes bewusste LAN und jeder öffentliche Hostname gehört hierher. |
| `FORWARDED_ALLOW_IPS` | IP-Adressen oder Netzwerke von Reverse-Proxys, deren `X-Forwarded-*`-Header vertrauenswürdig sein können. Verwenden Sie niemals standardmäßig `*` an einem exponierten Port. |
| `ALLOWED_ORIGINS` | Für Statusänderungen und Passkey-Zeremonien werden genaue Browser-Ursprünge akzeptiert. Die normale PWA bleibt vom gleichen Ursprung; Verwenden Sie niemals einen Platzhalter. |
| `SESSION_HTTPS_ONLY` | Fügt Browser-Sitzungscookies das Secure-Flag hinzu und ist für die HTTPS-Offenlegung obligatorisch. |
| `PUBLIC_EXPOSURE_ACKNOWLEDGED` | Eine ausdrückliche Bestätigung des Bedieners ist erst erforderlich, nachdem die gesamte öffentliche Checkliste durchlaufen wurde. |
| `PUBLISHED_ADDRESS` | Host-Bindung für Port 9380 erstellen; Vermeiden Sie eine öffentliche Umgehung des Reverse-Proxys. |

Beispielhafte Zielkonfiguration für einen kanonischen Host:

```env
PUBLIC_URL=https://vorrio.example.com
DEPLOYMENT_PROFILE=private_https
TRUSTED_HOSTS=vorrio.example.com
FORWARDED_ALLOW_IPS=172.20.0.0/16
ALLOWED_ORIGINS=https://vorrio.example.com
SESSION_HTTPS_ONLY=true
PUBLIC_EXPOSURE_ACKNOWLEDGED=false
```

Wenn zwei HTTPS-Namen absichtlich unterstützt werden, müssen beide aufgeführt werden:

```env
TRUSTED_HOSTS=vorrio.example.com,vorrio.internal.example.com
ALLOWED_ORIGINS=https://vorrio.example.com,https://vorrio.internal.example.com
```

## Reverse-Proxy-Vertrag

- Verwenden Sie einen dedizierten Hostnamen, keinen abgespeckten Pfad wie `/vorrio`;
- TLS an einem gepflegten Reverse-Proxy oder Tunnel beenden;
- Den ursprünglichen `Host`-Header beibehalten;
- Ersetzen Sie nicht vertrauenswürdige Clientwerte, anstatt sie anzuhängen.
  `X-Forwarded-For`, `X-Forwarded-Proto` und `X-Forwarded-Host`;
- Weitergeleiteten Headern nur von der tatsächlichen Proxy-Adresse oder dem tatsächlichen Netzwerk vertrauen;
- Anforderungstexte bis zum konfigurierten Empfangslimit weiterleiten;
- Halten Sie `/data`, API-Schlüssel und den internen Port des Containers privat;
- Überprüfen Sie `/api/health`, melden Sie sich an, laden Sie `/docs` über den öffentlichen Hostnamen hoch.
- Setzen Sie `PUBLIC_EXPOSURE_ACKNOWLEDGED=true` erst nach diesen Prüfungen und dem
  [Sicherheitsüberprüfung für externen Zugriff](EXTERNAL-ACCESS-SECURITY-REVIEW.md).

## HTTP 400 diagnostizieren

`TrustedHostMiddleware` gibt bei der Anfrage absichtlich 400 zurück
Der Hostname fehlt in `TRUSTED_HOSTS`. Die Lösung besteht darin, den echten Hostnamen hinzuzufügen.
die Validierung nicht global zu deaktivieren. Häufige Ursachen sind:

1. Es ist nur der LAN-Hostname zulässig, es wird jedoch die öffentliche Domäne verwendet.
2. Der Reverse-Proxy ersetzt `Host` durch seinen internen Upstream-Namen;
3. Ein öffentlicher Web-Ursprung versucht, einen privaten LAN-Ursprung aufzurufen und löst den Browser aus
   CORS oder Private Network Access-Schutz;
4. In `FORWARDED_ALLOW_IPS` fehlt eine Proxy-Adresse, was zu einer falschen Angabe führt
   Schema oder Weiterleitungsgenerierung.

`/api/health` ist die Lebendigkeitsprüfung. `/api/readiness` berichtet separat
Datenbank, Sitzungsgeheimnis, Host, Proxy, Cookie, kanonische URL und Exposure-Gate
Status. Ein unvollständiges `public_https`-Profil gibt HTTP 503 für die Anwendung zurück
Verkehr; Umgehen Sie diesen Fehler nicht, indem Sie ein schwächeres Profil für ein Publikum auswählen
Route.
