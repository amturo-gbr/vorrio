import { readFile, readdir } from "node:fs/promises";
import { createHash } from "node:crypto";
import path from "node:path";
import { fileURLToPath } from "node:url";

const docsDir = path.resolve(path.dirname(fileURLToPath(import.meta.url)), "..");
const localeDirs = Object.fromEntries(["de", "en"].map((locale) => [locale, path.join(docsDir, locale)]));

const markdownFiles = async (directory) =>
  (await readdir(directory)).filter((file) => file.endsWith(".md")).sort();

const [deFiles, enFiles] = await Promise.all([markdownFiles(localeDirs.de), markdownFiles(localeDirs.en)]);
const failures = [];
let sourceLock = {};
try {
  sourceLock = JSON.parse(await readFile(path.join(docsDir, "i18n-source-lock.json"), "utf8"));
} catch {
  failures.push("i18n-source-lock.json is missing or invalid; regenerate the translations");
}

if (JSON.stringify(deFiles) !== JSON.stringify(enFiles)) {
  failures.push(`Locale file sets differ:\nde=${deFiles.join(",")}\nen=${enFiles.join(",")}`);
}

const extractCode = (source) => [
  ...source.matchAll(/```[\s\S]*?```|~~~[\s\S]*?~~~/g),
  ...source.matchAll(/`[^`\n]+`/g),
].map((match) => match[0]);
const extractDestinations = (source) => [...source.matchAll(/\]\(([^)]+)\)/g)].map((match) => match[1]);
const proseOnly = (source) => source
  .replace(/^---\n[\s\S]*?\n---\n/, "")
  .replace(/```[\s\S]*?```|~~~[\s\S]*?~~~/g, "")
  .replace(/`[^`\n]+`/g, "")
  .replace(/\]\([^)]+\)/g, "]");
const frontmatterField = (source, field) => source.match(new RegExp(`^${field}:\\s*(.+)$`, "m"))?.[1]?.trim();

for (const file of enFiles) {
  const [deSource, enSource] = await Promise.all([
    readFile(path.join(localeDirs.de, file), "utf8"),
    readFile(path.join(localeDirs.en, file), "utf8"),
  ]);

  const sourceHash = createHash("sha256").update(enSource).digest("hex");
  if (sourceLock[file] !== sourceHash) failures.push(`${file}: German translation is stale`);

  if (!/^#\s+\S/m.test(deSource) || !/^#\s+\S/m.test(enSource)) failures.push(`${file}: missing H1`);
  if (deSource.trim() === enSource.trim()) failures.push(`${file}: German and English files are identical`);
  for (const field of ["title", "description"]) {
    const deValue = frontmatterField(deSource, field);
    const enValue = frontmatterField(enSource, field);
    if (enValue && (!deValue || deValue === enValue)) failures.push(`${file}: German ${field} is missing or untranslated`);
  }
  if (JSON.stringify(extractCode(deSource)) !== JSON.stringify(extractCode(enSource))) {
    failures.push(`${file}: fenced or inline technical code differs between locales`);
  }
  if (JSON.stringify(extractDestinations(deSource)) !== JSON.stringify(extractDestinations(enSource))) {
    failures.push(`${file}: link destinations differ between locales`);
  }

  const deProse = proseOnly(deSource);
  const residue = deProse.match(/\b(?:the|and|with|without|your|this|that|from|into|before|after|should|must|overview|installation|configuration)\b/gi) ?? [];
  const wordCount = deProse.split(/\s+/).filter(Boolean).length;
  if (wordCount > 120 && residue.length / wordCount > 0.025) {
    failures.push(`${file}: likely untranslated English prose (${residue.length}/${wordCount} common English words)`);
  }
}

if (JSON.stringify(Object.keys(sourceLock).sort()) !== JSON.stringify(enFiles)) {
  failures.push("i18n-source-lock.json does not match the English page set");
}

const rootMarkdown = (await readdir(docsDir)).filter((file) => file.endsWith(".md"));
if (JSON.stringify(rootMarkdown) !== JSON.stringify(["index.md"])) {
  failures.push(`Only the locale redirect may remain at docs root; found ${rootMarkdown.join(", ")}`);
}

if (failures.length) {
  console.error(failures.join("\n"));
  process.exit(1);
}

console.log(`Documentation locales are complete (${enFiles.length} paired pages; technical snippets and links match).`);
