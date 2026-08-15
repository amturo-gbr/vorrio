# AI providers and models

The backend supports OpenAI-compatible Chat Completions APIs, Anthropic's
Messages API and local OpenAI-compatible endpoints such as Ollama. The selected
provider receives the rendered receipt pages and, for digital PDFs, locally
extracted text. Secrets remain in the backend.

Remote provider error bodies also remain at that boundary. Vorrio shows only
the HTTP status category and a short hint for credentials, endpoint,
rate-limit or service availability; arbitrary third-party response content is
never rendered in the PWA.

## OpenAI presets

The settings screen keeps the current model until the user explicitly changes
it and offers these presets:

- `gpt-5.4-mini`: recommended balance for receipt vision and structured JSON;
- `gpt-5-mini`: economical established alternative;
- `gpt-5.6-luna`: low-cost latest-family option;
- `gpt-5.6-terra`: higher-quality option when cost is secondary;
- custom model ID: keeps experiments and future models possible.

All providers must support image input. A cheaper text-only model is not enough
for photographed receipts. Local models keep images on the household network,
but accuracy and required RAM/GPU depend heavily on the chosen vision model.

Changing a model does not change catalog or stock data. It only affects future
analyses; review and confirmation rules are provider-independent.

## Product-candidate ranking

When a household member explicitly opens an unresolved receipt line, Vorrio can
ask Open Facts for real product records. The selected AI provider receives only
the normalized line, retailer/store label, recognized brand, quantity, receipt
unit price and a reduced list of returned candidate metadata. It does not
receive candidate images or the complete receipt again.

The model must return only identifiers from that supplied list plus confidence
and a short reason. Vorrio combines this with deterministic name, brand,
package and retailer evidence. Provider failure leaves the real candidates in
their deterministic order. The model can never create or automatically assign
a product, barcode, image or price. When Open Facts supplies suitable images,
the final three-card review preserves up to two image-backed records even if
the optional AI order would otherwise hide all of them.

For digital PDFs, the embedded text order is also part of the extraction
contract: a quantity or unit-price continuation line belongs only to the
immediately preceding printed product. Ambiguous continuation lines must stay
unassigned instead of being shifted to another item.
