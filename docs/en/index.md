---
title: Welcome to Vorrio
description: Install, configure and operate the self-hosted Vorrio household inventory.
outline: [2, 3]
---

# Welcome to Vorrio

Vorrio turns reviewed receipts and package scans into dependable household stock. It is self-hosted, open source and designed to keep every stock-changing decision visible.

This documentation is generated from the same repository as the application. You can read the complete guide and API contract without access to a running or private Vorrio installation.

## Start in three steps

### 1. Prepare the installation

Vorrio requires Docker Engine with Compose v2 and persistent local storage. Clone the repository and create the local environment file:

```bash
git clone https://github.com/amturo-gbr/vorrio.git
cd vorrio
cp .env.example .env
openssl rand -hex 32
```

Store the generated value as `APP_SECRET_KEY` in `.env`. Never commit that file.

### 2. Start Vorrio

```bash
docker compose up -d --build
```

Open `http://localhost:9380`, create the first Owner and configure an analysis provider. Camera scanning and passkeys require a stable HTTPS origin.

### 3. Review the first purchase

Upload a receipt or scan a package, check the proposed product mapping and confirm only the intended changes. Vorrio never changes stock merely because an AI provider or product database returned a possible match.

::: tip Open source and under your control
Vorrio is released under `AGPL-3.0-or-later`. Household data stays in the storage you operate; optional providers and integrations are configured deliberately.
:::

## Choose your path

| If you want to… | Continue with… |
|---|---|
| Install a new household instance | [Installation](INSTALLATION.md) |
| Understand required and optional settings | [Configuration](CONFIGURATION.md) |
| Learn the receipt, scan, stock and shopping flow | [Daily workflow](WORKFLOW.md) |
| Expose Vorrio through HTTPS | [Deployment profiles](DEPLOYMENT-PROFILES.md) |
| Back up or restore the installation | [Backup and restore](BACKUP-RESTORE.md) |
| Build an integration | [Static API reference](api-reference.md) |
| Contribute another language | [Translation community](TRANSLATION-COMMUNITY.md) |

## Public documentation boundary

This site contains public product and operator documentation only. It does not connect to a household, expose a private API token or provide an interactive request console. The API reference is rendered statically from [`docs/api/openapi.json`](https://github.com/amturo-gbr/vorrio/blob/main/docs/api/openapi.json).

## What to read next

Begin with [Getting started](GETTING-STARTED.md) for the product model and first-login flow, then use [Installation](INSTALLATION.md) for a production-ready setup.
