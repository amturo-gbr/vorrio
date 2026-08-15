import { mkdir, readFile, readdir, writeFile } from "node:fs/promises";
import { createHash } from "node:crypto";
import path from "node:path";
import { fileURLToPath } from "node:url";

const docsDir = path.resolve(path.dirname(fileURLToPath(import.meta.url)), "..");
const sourceDir = path.join(docsDir, "en");
const targetDir = path.join(docsDir, "de");
const sourceLockPath = path.join(docsDir, "i18n-source-lock.json");
const force = process.argv.includes("--force");
const requestedFile = process.argv.find((argument) => argument.startsWith("--file="))?.slice("--file=".length);

const sleep = (milliseconds) => new Promise((resolve) => setTimeout(resolve, milliseconds));

function splitForTransport(value, limit = 300) {
  const chunks = [];
  let remaining = value;
  while (remaining.length > limit) {
    let boundary = remaining.lastIndexOf("\n\n", limit);
    if (boundary < limit * 0.45) boundary = remaining.lastIndexOf("\n", limit);
    if (boundary < limit * 0.45) boundary = limit;
    chunks.push(remaining.slice(0, boundary));
    remaining = remaining.slice(boundary);
  }
  if (remaining) chunks.push(remaining);
  return chunks;
}

function protectTechnicalText(value) {
  const tokens = [];
  const protect = (match) => {
    const token = `https://vorrio.invalid/t/${tokens.length}`;
    tokens.push(match);
    return token;
  };

  const technicalPattern = /^:::\s*(?:tip|warning|danger|info|details)?|\((?:https?:\/\/|\/|\.\/|\.\.\/|#[^)\n]*|[^)\n]*\.md(?:#[^)\n]*)?)[^)\n]*\)|`[^`\n]+`|<[^>\n]+>|https?:\/\/[^\s)>]+|(?<![\w])\/(?:api|auth|health|docs|openapi)[A-Za-z0-9_./{}:~-]*/gm;
  const protectedValue = value.replace(technicalPattern, protect);

  return {
    protectedValue,
    restore(translated) {
      let restored = translated;
      tokens.forEach((tokenValue, index) => {
        const token = `https://vorrio.invalid/t/${index}`;
        if (!restored.includes(token)) {
          const candidates = restored.match(/https:\/\/[^\s)>]+/g)?.join(", ") ?? "none";
          throw new Error(`Translation provider changed protected token ${index} (${tokenValue}); candidates: ${candidates}; output: ${restored.slice(0, 500)}`);
        }
        restored = restored.replaceAll(token, tokenValue);
      });
      return restored;
    },
  };
}

async function translateChunk(value) {
  if (!/[A-Za-z]/.test(value)) return value;
  const endpoint = new URL("https://translate.googleapis.com/translate_a/single");
  endpoint.search = new URLSearchParams({
    client: "gtx",
    sl: "en",
    tl: "de",
    dt: "t",
    q: value,
  }).toString();

  let lastError;
  for (let attempt = 1; attempt <= 5; attempt += 1) {
    try {
      const response = await fetch(endpoint, { headers: { "user-agent": "Vorrio documentation translator" } });
      if (!response.ok) throw new Error(`HTTP ${response.status}`);
      const payload = await response.json();
      return payload[0].map((entry) => entry[0]).join("");
    } catch (error) {
      lastError = error;
      await sleep(350 * attempt);
    }
  }
  throw lastError;
}

async function translateProse(value) {
  const translated = [];
  for (const chunk of splitForTransport(value)) {
    const leadingWhitespace = chunk.match(/^\s*/)?.[0] ?? "";
    const trailingWhitespace = chunk.match(/\s*$/)?.[0] ?? "";
    const contentEnd = chunk.length - trailingWhitespace.length;

    if (contentEnd <= leadingWhitespace.length) {
      translated.push(chunk);
      continue;
    }

    const content = chunk.slice(leadingWhitespace.length, contentEnd);
    const { protectedValue, restore } = protectTechnicalText(content);
    translated.push(`${leadingWhitespace}${restore(await translateChunk(protectedValue))}${trailingWhitespace}`);
    await sleep(80);
  }
  return translated.join("")
    .replaceAll("Docker komponieren", "Docker Compose")
    .replaceAll("Docker-Compose", "Docker Compose")
    .replaceAll("Vorrio-Dokumente", "Vorrio Docs");
}

async function translateMarkdown(source) {
  let frontmatter = "";
  let body = source;
  const frontmatterMatch = body.match(/^---\n[\s\S]*?\n---\n/);
  if (frontmatterMatch) {
    const translatedLines = [];
    for (const line of frontmatterMatch[0].split("\n")) {
      const localizedField = line.match(/^(title|description):\s*(.+)$/);
      translatedLines.push(localizedField
        ? `${localizedField[1]}: ${await translateProse(localizedField[2])}`
        : line);
    }
    frontmatter = translatedLines.join("\n");
    body = body.slice(frontmatterMatch[0].length);
  }

  const parts = body.split(/(```[\s\S]*?```|~~~[\s\S]*?~~~)/g);
  const translatedParts = [];
  for (const part of parts) {
    if (!part) continue;
    translatedParts.push(part.startsWith("```") || part.startsWith("~~~") ? part : await translateProse(part));
  }
  return `${frontmatter}${translatedParts.join("")}`;
}

await mkdir(targetDir, { recursive: true });
const sourceFiles = (await readdir(sourceDir))
  .filter((file) => file.endsWith(".md") && (!requestedFile || file === requestedFile))
  .sort();

if (requestedFile && sourceFiles.length === 0) {
  throw new Error(`Unknown documentation file: ${requestedFile}`);
}

let sourceLock = {};
try {
  sourceLock = JSON.parse(await readFile(sourceLockPath, "utf8"));
} catch {
  if (requestedFile) throw new Error("Run a complete translation once before updating a single file");
}
const bootstrapLock = Object.keys(sourceLock).length === 0;

for (const file of sourceFiles) {
  const target = path.join(targetDir, file);
  if (!force) {
    try {
      await readFile(target, "utf8");
      console.log(`Keeping existing translation: ${file}`);
      if (bootstrapLock) {
        const source = await readFile(path.join(sourceDir, file), "utf8");
        sourceLock[file] = createHash("sha256").update(source).digest("hex");
      }
      continue;
    } catch {
      // Translate a missing file.
    }
  }
  const source = await readFile(path.join(sourceDir, file), "utf8");
  const translated = await translateMarkdown(source);
  await writeFile(target, translated, "utf8");
  sourceLock[file] = createHash("sha256").update(source).digest("hex");
  console.log(`Translated ${file}`);
}

await writeFile(
  sourceLockPath,
  `${JSON.stringify(Object.fromEntries(Object.entries(sourceLock).sort()), null, 2)}\n`,
  "utf8",
);
