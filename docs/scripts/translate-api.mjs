import { createHash } from "node:crypto";
import { readFile, writeFile } from "node:fs/promises";
import path from "node:path";
import { fileURLToPath } from "node:url";

const docsDir = path.resolve(path.dirname(fileURLToPath(import.meta.url)), "..");
const sourcePath = path.join(docsDir, "api", "openapi.json");
const targetPath = path.join(docsDir, "api", "openapi.de.json");
const sourceBytes = await readFile(sourcePath);
const specification = JSON.parse(sourceBytes.toString("utf8"));
const methods = new Set(["get", "post", "put", "patch", "delete"]);

const tagTranslations = {
  System: "System",
  Authentication: "Authentifizierung",
  Catalog: "Katalog",
  Experience: "Nutzungserlebnis",
  "Legacy Grocy": "Grocy-Kompatibilität",
  Insights: "Auswertungen",
  Integrations: "Integrationen",
  Notifications: "Benachrichtigungen",
  "Privacy & Operations": "Datenschutz und Betrieb",
  Receipts: "Kassenbons",
  Scanning: "Scannen",
  Settings: "Einstellungen",
  Shopping: "Einkäufe",
  Stock: "Vorrat",
};

const sleep = (milliseconds) => new Promise((resolve) => setTimeout(resolve, milliseconds));

function protectTechnicalText(value) {
  const tokens = [];
  const protectedValue = value.replace(
    /\/api\/[A-Za-z0-9_./{}:~-]*|\b(?:Vorrio|OpenAPI|SHA-256|BCP 47|PWA|Web Push|Open Facts|EAN|UPC|GTIN|EUR|POST|GET|PUT|PATCH|DELETE|client_mutation_id)\b/g,
    (match) => {
      const token = `https://vorrio.invalid/t/${tokens.length}`;
      tokens.push(match);
      return token;
    },
  );
  return {
    protectedValue,
    restore(translated) {
      return tokens.reduce(
        (result, token, index) => result.replaceAll(`https://vorrio.invalid/t/${index}`, token),
        translated,
      );
    },
  };
}

async function translate(value) {
  if (!value) return "";
  const { protectedValue, restore } = protectTechnicalText(value);
  const endpoint = new URL("https://translate.googleapis.com/translate_a/single");
  endpoint.search = new URLSearchParams({ client: "gtx", sl: "en", tl: "de", dt: "t", q: protectedValue }).toString();
  let lastError;
  for (let attempt = 1; attempt <= 5; attempt += 1) {
    try {
      const response = await fetch(endpoint, { headers: { "user-agent": "Vorrio API documentation translator" } });
      if (!response.ok) throw new Error(`HTTP ${response.status}`);
      const payload = await response.json();
      return restore(payload[0].map((entry) => entry[0]).join(""));
    } catch (error) {
      lastError = error;
      await sleep(300 * attempt);
    }
  }
  throw lastError;
}

const entries = [];
for (const [apiPath, pathItem] of Object.entries(specification.paths)) {
  for (const [method, operation] of Object.entries(pathItem)) {
    if (!methods.has(method)) continue;
    entries.push({ key: `${method} ${apiPath}`, operation });
  }
}

const operations = {};
for (let offset = 0; offset < entries.length; offset += 5) {
  const batch = entries.slice(offset, offset + 5);
  const translated = await Promise.all(batch.map(async ({ key, operation }) => ({
    key,
    summary: await translate(operation.summary ?? operation.operationId ?? key),
    description: await translate(operation.description ?? ""),
  })));
  for (const operation of translated) operations[operation.key] = operation;
  console.log(`Translated ${Math.min(offset + batch.length, entries.length)} / ${entries.length} API operations`);
  await sleep(120);
}

await writeFile(targetPath, `${JSON.stringify({
  sourceSha256: createHash("sha256").update(sourceBytes).digest("hex"),
  tags: tagTranslations,
  operations,
}, null, 2)}\n`, "utf8");
console.log(`Updated ${path.relative(docsDir, targetPath)}`);
