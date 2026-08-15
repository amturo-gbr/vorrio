---
title: Willkommen bei Vorrio
description: Vorrio selbst hosten, konfigurieren und den Haushaltsvorrat zuverlässig verwalten.
outline: [2, 3]
---

# Willkommen in Vorrio

Vorrio verwandelt geprüfte Kassenbons und Packungsscans in einen verlässlichen Haushaltsvorrat. Es ist selbst gehostet, Open Source und so konzipiert, dass jede Bestandsänderung nachvollziehbar bleibt.

Diese Dokumentation wird aus demselben Repository wie die Anwendung generiert. Sie können die vollständige Anleitung und den API-Vertrag lesen, ohne Zugriff auf eine laufende oder private Vorrio-Installation zu haben.

## Beginnen Sie in drei Schritten

### 1. Bereiten Sie die Installation vor

Vorrio erfordert Docker Engine mit Compose v2 und persistentem lokalem Speicher. Klonen Sie das Repository und erstellen Sie die lokale Umgebungsdatei:

```bash
git clone https://github.com/amturo-gbr/vorrio.git
cd vorrio
cp .env.example .env
openssl rand -hex 32
```

Speichern Sie den generierten Wert als `APP_SECRET_KEY` in `.env`. Übertragen Sie diese Datei niemals.

### 2. Starten Sie Vorrio

```bash
docker compose up -d --build
```

Öffnen Sie `http://localhost:9380`, erstellen Sie den ersten Eigentümer und konfigurieren Sie einen Analyseanbieter. Kamerascans und Passkeys erfordern einen stabilen HTTPS-Ursprung.

### 3. Überprüfen Sie den ersten Kauf

Laden Sie eine Quittung hoch oder scannen Sie ein Paket, überprüfen Sie die vorgeschlagene Produktzuordnung und bestätigen Sie nur die beabsichtigten Änderungen. Vorrio ändert niemals den Lagerbestand, nur weil ein KI-Anbieter oder eine Produktdatenbank eine mögliche Übereinstimmung zurückgegeben hat.

::: tip Open Source und unter Ihrer Kontrolle
Vorrio ist unter `AGPL-3.0-or-later` veröffentlicht. Haushaltsdaten bleiben in dem von Ihnen betriebenen Speicher; optionale Anbieter und Integrationen werden bewusst konfiguriert.
:::

## Wählen Sie Ihren Weg

| Wenn Sie möchten… | Weiter mit… |
|---|---|
| Installieren Sie eine neue Haushaltsinstanz | [Installation](INSTALLATION.md) |
| Erforderliche und optionale Einstellungen verstehen | [Konfiguration](CONFIGURATION.md) |
| Erfahren Sie mehr über den Beleg, den Scan, den Lagerbestand und den Einkaufsablauf | [Täglicher Arbeitsablauf](WORKFLOW.md) |
| Vorrio über HTTPS verfügbar machen | [Bereitstellungsprofile](DEPLOYMENT-PROFILES.md) |
| Sichern oder wiederherstellen Sie die Installation | [Sichern und Wiederherstellen](BACKUP-RESTORE.md) |
| Erstellen Sie eine Integration | [Statische API-Referenz](api-reference.md) |
| Eine andere Sprache beisteuern | [Übersetzungsgemeinschaft](TRANSLATION-COMMUNITY.md) |

## Grenze der öffentlichen Dokumentation

Diese Website enthält ausschließlich öffentliche Produkt- und Betreiberdokumentation. Sie stellt keine Verbindung zu einem Haushalt her, gibt kein privates API-Token aus und bietet keine interaktive Anfragekonsole. Die API-Referenz wird statisch aus [`docs/api/openapi.json`](https://github.com/amturo-gbr/vorrio/blob/main/docs/api/openapi.json) erzeugt.

## Was Sie als nächstes lesen sollten

Beginnen Sie mit [Erste Schritte](GETTING-STARTED.md) für das Produktmodell und den Ablauf der ersten Anmeldung und verwenden Sie dann [Installation](INSTALLATION.md) für ein produktionsbereites Setup.
