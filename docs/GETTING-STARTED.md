# Getting started in Vorrio

Vorrio has one primary story:

```text
purchase -> review -> local product knowledge -> stock -> shopping
```

Nothing changes stock merely because an AI model or product database found a
possible match. Vorrio first presents the result and its evidence; a household
member confirms the intended product and action.

## Language

The signed-out screen initially follows the browser and supports German and
English. First-run setup and invitation acceptance store that language for the
new account. After sign-in, each user's saved choice is authoritative across
devices and can be changed under **Settings → Language & region**.

Changing the interface never translates or rewrites household product names,
brands, store names, receipt text, currency or the server timezone. See
[Localization](LOCALIZATION.md) for the exact behavior.

## First login

After an Owner creates the installation, and after every invited account's first
login, Vorrio opens a three-step introduction:

1. **The main flow** explains how a receipt becomes reviewed stock.
2. **The two input paths** distinguish a whole purchase from one package scan.
3. **The safety boundary** explains that suggestions remain proposals until a
   person confirms them.

The final action goes directly to receipt capture or package scanning. A Viewer
is taken to the read-only stock workspace instead. **Später** closes the guide
without falsely marking it complete; it appears again at the next login until a
final start action is chosen. It can always be reopened from
**Einstellungen → Hilfe & Version**.

## Where to find things

| Area | Use it for |
|---|---|
| **Start** | Photograph a complete receipt, upload an image/PDF and reopen recent receipts. |
| **Scannen** | Identify one barcode, add or consume stock, mark a package open or add it to the shopping list. |
| **Vorrat** | Find and edit products, variants, barcodes, images, locations and current quantities. |
| **Einkäufe** | Use the shopping list, low-stock proposals, price history, budget and receipt history. |
| **Einstellungen** | Manage the account, family, security, notifications, optional connectors, privacy, operations and help. |

## After an update

The operator still controls Docker updates. Vorrio does not pull or restart its
own container. When a new image is deliberately deployed and its application
version changes, each account sees the installed version's concise release
notes once after login. Acknowledgement is stored per user in the server
database, so switching browsers or installing the PWA does not repeat it.

Closing with **Später lesen** does not acknowledge the release; it can appear
again after a later login. **Verstanden** records the running version. Current
notes remain available from **Einstellungen → Hilfe & Version → Was ist neu?**.

Vorrio reports what is already installed. It does not contact GitHub or a
registry to announce an available update, and it does not imply that `latest`
was pulled successfully. Operators should keep using the documented backup,
pull, recreate and health/readiness checks in [Installation](INSTALLATION.md).

## Account and data behavior

- Introduction completion and acknowledged version belong to the user, not the
  browser.
- The state contains no password, token or household content.
- Portable export includes it with personal preferences.
- Complete installation erasure deletes it.
- Automation tokens cannot read or change it.
