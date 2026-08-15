import { access, readFile, readdir } from "node:fs/promises";
import path from "node:path";
import { fileURLToPath } from "node:url";

const docsDir = path.resolve(path.dirname(fileURLToPath(import.meta.url)), "..");
const distDir = path.join(docsDir, ".vitepress", "dist");
const failures = [];

const htmlFiles = async (locale) =>
  (await readdir(path.join(distDir, locale))).filter((file) => file.endsWith(".html")).sort();

const [deFiles, enFiles] = await Promise.all([htmlFiles("de"), htmlFiles("en")]);
if (JSON.stringify(deFiles) !== JSON.stringify(enFiles)) failures.push("Built locale page sets differ");

for (const file of enFiles) {
  for (const locale of ["de", "en"]) {
    const html = await readFile(path.join(distDir, locale, file), "utf8");
    const route = file === "index.html" ? "" : file.replace(/\.html$/, "");
    const canonical = `https://docs.vorrio.app/${locale}/${route}`;
    if (!html.includes(`<html lang="${locale === "de" ? "de-DE" : "en-US"}"`)) {
      failures.push(`${locale}/${file}: wrong html lang`);
    }
    if (!html.includes(`rel="canonical" href="${canonical}"`)) failures.push(`${locale}/${file}: canonical missing`);
    for (const alternate of ["de", "en", "x-default"]) {
      if (!html.includes(`hreflang="${alternate}"`)) failures.push(`${locale}/${file}: hreflang ${alternate} missing`);
    }
  }
}

const rootHtml = await readFile(path.join(distDir, "index.html"), "utf8");
if (!rootHtml.includes("Sprache wählen") || !rootHtml.includes("Choose language")) {
  failures.push("Root locale chooser is missing its no-JavaScript fallback");
}

for (const asset of ["openapi.json", "sitemap.xml", "robots.txt"]) {
  try {
    await access(path.join(distDir, asset));
  } catch {
    failures.push(`${asset}: missing from built documentation`);
  }
}

if (failures.length) {
  console.error(failures.join("\n"));
  process.exit(1);
}

console.log(`Built documentation i18n is valid (${enFiles.length * 2} localized HTML pages with canonical and hreflang tags).`);

