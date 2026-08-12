# REST API

Vorrio exposes a versioned JSON API under `/api/v1`. The PWA uses the same
contract as external integrations. Browser authentication uses a signed
HttpOnly cookie with a random token backed by a revocable server session.

- Swagger UI: `/docs`
- ReDoc: `/redoc`
- OpenAPI 3.1 contract: `/openapi.json`
- Health check: `/api/health`
- Deployment readiness: `/api/readiness`

The generated contract is stored in `docs/api/openapi.json`. Run
`make api-docs` after every API change and `make api-docs-check` before
submitting a change.

## Endpoints

| Method | Path | Group | Summary | Deprecated |
|---|---|---|---|---|
| `GET` | `/api/health` | System | Check instance health | no |
| `GET` | `/api/readiness` | System | Check deployment readiness | no |
| `GET` | `/api/v1/auth/api-token-scopes` | Authentication | List available automation-token scopes | no |
| `GET` | `/api/v1/auth/api-tokens` | Authentication | List the current account's automation tokens | no |
| `POST` | `/api/v1/auth/api-tokens` | Authentication | Create a scoped automation token | no |
| `DELETE` | `/api/v1/auth/api-tokens/{token_id}` | Authentication | Revoke one automation token | no |
| `GET` | `/api/v1/auth/invitations` | Authentication | List active household invitations | no |
| `POST` | `/api/v1/auth/invitations` | Authentication | Create a single-use household invitation | no |
| `DELETE` | `/api/v1/auth/invitations/{invitation_id}` | Authentication | Revoke an unused household invitation | no |
| `GET` | `/api/v1/auth/invitations/{token}` | Authentication | Read a single-use invitation | no |
| `POST` | `/api/v1/auth/invitations/{token}/accept` | Authentication | Accept an invitation and create the member account | no |
| `POST` | `/api/v1/auth/login` | Authentication | Create a household session | no |
| `POST` | `/api/v1/auth/logout` | Authentication | End the current session | no |
| `GET` | `/api/v1/auth/me` | Authentication | Validate the current session | no |
| `GET` | `/api/v1/auth/members` | Authentication | List household members | no |
| `PATCH` | `/api/v1/auth/members/{user_id}` | Authentication | Change a member role or access state | no |
| `POST` | `/api/v1/auth/mfa/verify` | Authentication | Finish a password login with a second factor | no |
| `POST` | `/api/v1/auth/passkeys/authentication/begin` | Authentication | Start passwordless passkey authentication | no |
| `POST` | `/api/v1/auth/passkeys/authentication/complete` | Authentication | Complete passwordless passkey authentication | no |
| `POST` | `/api/v1/auth/passkeys/registration/begin` | Authentication | Start passkey registration | no |
| `POST` | `/api/v1/auth/passkeys/registration/complete` | Authentication | Verify and save a passkey | no |
| `DELETE` | `/api/v1/auth/passkeys/{credential_id}` | Authentication | Delete one passkey | no |
| `PUT` | `/api/v1/auth/password` | Authentication | Change the current account password | no |
| `PATCH` | `/api/v1/auth/preferences` | Authentication | Update personal interface preferences | no |
| `PATCH` | `/api/v1/auth/profile` | Authentication | Complete or update the owner profile | no |
| `POST` | `/api/v1/auth/reauthenticate` | Authentication | Confirm identity before a sensitive change | no |
| `POST` | `/api/v1/auth/recovery` | Authentication | Recover an account with a single-use recovery code | no |
| `POST` | `/api/v1/auth/recovery-codes` | Authentication | Replace all single-use recovery codes | no |
| `GET` | `/api/v1/auth/security` | Authentication | Read passkey, TOTP and recovery status | no |
| `GET` | `/api/v1/auth/sessions` | Authentication | List active browser sessions | no |
| `POST` | `/api/v1/auth/sessions/revoke-others` | Authentication | Revoke every other browser session | no |
| `DELETE` | `/api/v1/auth/sessions/{session_id}` | Authentication | Revoke one browser session | no |
| `POST` | `/api/v1/auth/setup` | Authentication | Complete first-run setup | no |
| `GET` | `/api/v1/auth/state` | Authentication | Read setup and session state | no |
| `DELETE` | `/api/v1/auth/totp` | Authentication | Disable authenticator-app verification | no |
| `POST` | `/api/v1/auth/totp/enable` | Authentication | Verify and enable an authenticator app | no |
| `POST` | `/api/v1/auth/totp/setup` | Authentication | Create a pending authenticator-app secret | no |
| `GET` | `/api/v1/catalog/barcodes/{barcode}/lookup` | Catalog | Resolve a barcode locally or through Open Facts | no |
| `GET` | `/api/v1/catalog/master-data` | Catalog | List locations, units and product groups | no |
| `POST` | `/api/v1/catalog/master-data/{kind}` | Catalog | Create a catalog master-data entry | no |
| `PATCH` | `/api/v1/catalog/master-data/{kind}/{item_id}` | Catalog | Rename or edit a catalog master-data entry | no |
| `DELETE` | `/api/v1/catalog/master-data/{kind}/{item_id}` | Catalog | Archive an unused catalog master-data entry | no |
| `GET` | `/api/v1/catalog/products` | Catalog | Search catalog products | no |
| `POST` | `/api/v1/catalog/products` | Catalog | Create a local catalog product | no |
| `GET` | `/api/v1/catalog/products/{product_id}` | Catalog | Read a product with variants and barcodes | no |
| `PATCH` | `/api/v1/catalog/products/{product_id}` | Catalog | Edit a local catalog product | no |
| `GET` | `/api/v1/catalog/products/{product_id}/image` | Catalog | Read a locally managed product image | no |
| `POST` | `/api/v1/catalog/products/{product_id}/image` | Catalog | Upload a private product image | no |
| `DELETE` | `/api/v1/catalog/products/{product_id}/image` | Catalog | Remove the current product image | no |
| `GET` | `/api/v1/catalog/products/{product_id}/price-history` | Catalog | List receipt prices for a catalog product | no |
| `POST` | `/api/v1/catalog/products/{product_id}/variants` | Catalog | Add a sellable product variant | no |
| `POST` | `/api/v1/catalog/reconcile` | Catalog | Re-evaluate unresolved receipt lines | no |
| `PATCH` | `/api/v1/catalog/variants/{variant_id}` | Catalog | Edit a product variant | no |
| `DELETE` | `/api/v1/catalog/variants/{variant_id}` | Catalog | Delete an unused product variant | no |
| `POST` | `/api/v1/catalog/variants/{variant_id}/barcodes` | Catalog | Attach a barcode to a product variant | no |
| `DELETE` | `/api/v1/catalog/variants/{variant_id}/barcodes/{barcode}` | Catalog | Detach a barcode from a product variant | no |
| `GET` | `/api/v1/experience` | Experience | Read personal onboarding and release-note state | no |
| `PUT` | `/api/v1/experience` | Experience | Complete onboarding or acknowledge the current release | no |
| `GET` | `/api/v1/grocy/master-data` | Legacy Grocy | Read Grocy master data | yes |
| `GET` | `/api/v1/grocy/products` | Legacy Grocy | Search Grocy products | yes |
| `GET` | `/api/v1/insights/budget` | Insights | Summarize the household budget from confirmed receipts | no |
| `PUT` | `/api/v1/insights/budget/settings` | Insights | Set or clear the shared monthly household budget | no |
| `GET` | `/api/v1/insights/prices` | Insights | Summarize confirmed receipt prices by product and store | no |
| `POST` | `/api/v1/integrations/grocy/import-catalog` | Integrations | Import or update the local catalog from Grocy | no |
| `GET` | `/api/v1/integrations/grocy/stock-preview` | Integrations | Preview mapped Grocy balances without changing Vorrio | no |
| `PUT` | `/api/v1/notifications/preferences` | Notifications | Update personal stock notification preferences | no |
| `GET` | `/api/v1/notifications/state` | Notifications | Read personal Web Push settings and devices | no |
| `POST` | `/api/v1/notifications/subscriptions` | Notifications | Register or refresh one browser push device | no |
| `DELETE` | `/api/v1/notifications/subscriptions/{subscription_id}` | Notifications | Revoke one personal push device | no |
| `POST` | `/api/v1/notifications/test` | Notifications | Send a visible test notification to one personal device | no |
| `GET` | `/api/v1/operations/overview` | Privacy & Operations | Read the privacy-safe owner operations overview | no |
| `GET` | `/api/v1/privacy/export` | Privacy & Operations | Download a secret-free portable household export | no |
| `GET` | `/api/v1/privacy/export/preview` | Privacy & Operations | Preview the portable household export | no |
| `DELETE` | `/api/v1/privacy/household` | Privacy & Operations | Permanently erase this single-household installation | no |
| `GET` | `/api/v1/privacy/retention` | Privacy & Operations | Preview receipt-file retention | no |
| `POST` | `/api/v1/privacy/retention/run` | Privacy & Operations | Apply receipt-file retention now | no |
| `GET` | `/api/v1/receipts` | Receipts | List recent receipts | no |
| `POST` | `/api/v1/receipts/analyze` | Receipts | Analyze an image or PDF receipt | no |
| `GET` | `/api/v1/receipts/{receipt_id}` | Receipts | Get a receipt with all lines | no |
| `POST` | `/api/v1/receipts/{receipt_id}/import` | Receipts | Commit reviewed lines to local stock | no |
| `PATCH` | `/api/v1/receipts/{receipt_id}/items/{item_id}` | Receipts | Map a receipt line to a catalog product | no |
| `POST` | `/api/v1/receipts/{receipt_id}/items/{item_id}/candidate` | Receipts | Confirm and learn a real product candidate | no |
| `GET` | `/api/v1/receipts/{receipt_id}/items/{item_id}/candidates` | Receipts | Find real product candidates for a receipt line | no |
| `POST` | `/api/v1/receipts/{receipt_id}/items/{item_id}/catalog-product` | Receipts | Create and map a local catalog product | no |
| `POST` | `/api/v1/receipts/{receipt_id}/items/{item_id}/create-product` | Legacy Grocy | Create and map a Grocy product | yes |
| `POST` | `/api/v1/scans/resolve` | Scanning | Resolve a package code without changing stock | no |
| `GET` | `/api/v1/scans/unresolved` | Scanning | List unresolved package scans | no |
| `GET` | `/api/v1/scans/{scan_id}` | Scanning | Read one scan draft | no |
| `PATCH` | `/api/v1/scans/{scan_id}` | Scanning | Edit or map an unresolved scan | no |
| `DELETE` | `/api/v1/scans/{scan_id}` | Scanning | Discard an unresolved scan | no |
| `POST` | `/api/v1/scans/{scan_id}/confirm` | Scanning | Confirm the selected package action | no |
| `GET` | `/api/v1/settings` | Settings | Read public settings | no |
| `PUT` | `/api/v1/settings` | Settings | Replace instance settings | no |
| `POST` | `/api/v1/settings/test-grocy` | Settings | Test the Grocy connector | no |
| `POST` | `/api/v1/settings/test-provider` | Settings | Test the selected analysis provider | no |
| `GET` | `/api/v1/shopping-list` | Shopping | List open household shopping items | no |
| `POST` | `/api/v1/shopping-list/generate` | Shopping | Generate reviewed shopping-list items from low stock | no |
| `GET` | `/api/v1/shopping-list/low-stock` | Shopping | Preview products below their configured minimum stock | no |
| `PATCH` | `/api/v1/shopping-list/{item_id}` | Shopping | Edit or complete a shopping-list item | no |
| `GET` | `/api/v1/status` | System | Read instance and connector status | no |
| `GET` | `/api/v1/stock/count/products` | Stock | List products for a reviewed stock count | no |
| `GET` | `/api/v1/stock/counts` | Stock | List completed stock counts | no |
| `POST` | `/api/v1/stock/counts` | Stock | Apply a reviewed opening or correction count | no |

## Compatibility

Pre-0.6 paths below `/api` are accepted temporarily by the server, but they are
not part of the canonical contract. New clients must use `/api/v1`.
