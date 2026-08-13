import fs from 'node:fs'
import path from 'node:path'
import ts from 'typescript'

const frontendRoot = path.resolve(import.meta.dirname, '..')
const sourceRoot = path.join(frontendRoot, 'src')
const catalog = JSON.parse(
  fs.readFileSync(path.join(sourceRoot, 'locales/en/translation.json'), 'utf8'),
)
const germanCatalog = JSON.parse(
  fs.readFileSync(path.join(sourceRoot, 'locales/de/translation.json'), 'utf8'),
)
const localeRoot = path.join(sourceRoot, 'locales')
const localeDirectories = fs.readdirSync(localeRoot, { withFileTypes: true })
  .filter((entry) => entry.isDirectory())
  .map((entry) => entry.name)
  .sort()
const localeManifests = Object.fromEntries(localeDirectories.map((locale) => [
  locale,
  JSON.parse(fs.readFileSync(path.join(localeRoot, locale, 'manifest.json'), 'utf8')),
]))
const registrySource = fs.readFileSync(path.join(localeRoot, 'registry.ts'), 'utf8')
const sourceFiles = fs.readdirSync(sourceRoot, { recursive: true })
  .filter((name) => /\.(?:ts|tsx)$/.test(name))

const translationKeys = new Set()
const untranslated = []
const visibleGerman = /[ÄÖÜäöüß]|\b(?:Abbrechen|Abmelden|Anmelden|Artikel|Bestand|Bon|Bons|Einkauf|Einkäufe|Einkaufsliste|Einheit|Einheiten|Eintrag|Einträge|Einstellungen|Entfernen|Fehler|Gerät|Geräte|Geschäft|Haushalt|Hinzufügen|Kamera|keine?|Lagerort|Menge|noch|Öffnen|Passwort|Preis|Produkt|Produkte|Scannen|Speichern|Sitzung|Verbrauchen|Vorrat|wurde|wurden|werden|Zurück)\b/i
const ignoredAttributes = new Set([
  'accept', 'autoComplete', 'capture', 'className', 'id', 'inputMode', 'key',
  'method', 'name', 'role', 'type',
])

const callName = (node, sourceFile) =>
  ts.isCallExpression(node) ? node.expression.getText(sourceFile) : ''

const insideLocalizedCall = (node, sourceFile) => {
  let current = node.parent
  while (current) {
    if (ts.isCallExpression(current) && ['translate', 't', 'countLabel'].includes(callName(current, sourceFile))) {
      return true
    }
    if (ts.isJsxElement(current) || ts.isJsxSelfClosingElement(current) || ts.isJsxFragment(current)) break
    current = current.parent
  }
  return false
}

const isVisibleContext = (node, sourceFile) => {
  let current = node.parent
  while (current) {
    if (ts.isJsxAttribute(current)) return !ignoredAttributes.has(current.name.getText(sourceFile))
    if (ts.isJsxExpression(current) || ts.isJsxElement(current) || ts.isJsxSelfClosingElement(current)) return true
    if (ts.isCallExpression(current)) {
      const name = callName(current, sourceFile)
      if (/set(?:Error|Message|Result)|onNotice|onSaved|confirm|Error$/.test(name)) return true
    }
    if (ts.isSourceFile(current) || ts.isFunctionDeclaration(current) || ts.isArrowFunction(current)) break
    current = current.parent
  }
  return false
}

const collectLiterals = (node) => {
  if (ts.isStringLiteral(node) || ts.isNoSubstitutionTemplateLiteral(node)) {
    translationKeys.add(node.text)
  }
  ts.forEachChild(node, collectLiterals)
}

const visibleText = (node) => {
  if (ts.isStringLiteral(node) || ts.isNoSubstitutionTemplateLiteral(node) || ts.isJsxText(node)) {
    return node.text
  }
  if (ts.isTemplateExpression(node)) {
    return [node.head.text, ...node.templateSpans.map((span) => span.literal.text)].join(' ')
  }
  return null
}

for (const relativeFile of sourceFiles) {
  const filename = path.join(sourceRoot, relativeFile)
  const sourceFile = ts.createSourceFile(
    filename,
    fs.readFileSync(filename, 'utf8'),
    ts.ScriptTarget.Latest,
    true,
    filename.endsWith('.tsx') ? ts.ScriptKind.TSX : ts.ScriptKind.TS,
  )

  const visit = (node) => {
    if (ts.isCallExpression(node) && ['translate', 't'].includes(callName(node, sourceFile)) && node.arguments[0]) {
      collectLiterals(node.arguments[0])
    }
    const candidate = visibleText(node)
    if (
      candidate !== null &&
      visibleGerman.test(candidate) &&
      !insideLocalizedCall(node, sourceFile) &&
      isVisibleContext(node, sourceFile) &&
      !/^\s|^[a-z0-9_-]+$/.test(candidate)
    ) {
      const position = sourceFile.getLineAndCharacterOfPosition(node.getStart(sourceFile))
      untranslated.push(`${relativeFile}:${position.line + 1}:${position.character + 1} ${JSON.stringify(candidate)}`)
    }
    ts.forEachChild(node, visit)
  }
  visit(sourceFile)
}

const missing = [...translationKeys]
  .filter((key) => !(key in catalog))
  .sort((left, right) => left.localeCompare(right, 'de'))
const empty = [...translationKeys]
  .filter((key) => !String(catalog[key] ?? '').trim())
  .sort((left, right) => left.localeCompare(right, 'de'))
const countedKeys = [...translationKeys].filter((key) => key.includes('{{count}}'))
const missingPluralForms = countedKeys.flatMap((key) => [
  ...['_one', '_other'].filter((suffix) => !(key + suffix in catalog)).map((suffix) => `en:${key + suffix}`),
  ...['_one', '_other'].filter((suffix) => !(key + suffix in germanCatalog)).map((suffix) => `de:${key + suffix}`),
]).sort((left, right) => left.localeCompare(right, 'de'))
const semanticKeys = [...translationKeys].filter((key) => /^[a-z][a-z0-9]*(?:\.[a-z0-9_-]+)+$/.test(key))
const legacyKeys = [...translationKeys].filter((key) => !semanticKeys.includes(key))
const maximumLegacyKeys = 746
const invalidManifests = localeDirectories.flatMap((locale) => {
  const manifest = localeManifests[locale]
  const errors = []
  if (manifest.locale !== locale) errors.push(`${locale}: manifest locale must match its directory`)
  if (manifest.tier !== 'official') errors.push(`${locale}: bundled locale must be official`)
  if (manifest.completion !== 100) errors.push(`${locale}: bundled locale must be 100% complete`)
  if (!registrySource.includes(`${locale}: definition(`)) errors.push(`${locale}: missing lazy registry entry`)
  return errors
})
const missingSemanticFallbacks = semanticKeys.flatMap((key) => [
  ...(!(key in catalog) ? [`en:${key}`] : []),
  ...(!(key in germanCatalog) ? [`de:${key}`] : []),
])

console.log(JSON.stringify({
  translatedKeysUsed: translationKeys.size,
  englishCatalogKeys: Object.keys(catalog).length,
  germanPluralKeys: Object.keys(germanCatalog).length,
  missing: missing.length,
  empty: empty.length,
  missingPluralForms: missingPluralForms.length,
  semanticKeys: semanticKeys.length,
  legacyKeys: legacyKeys.length,
  invalidManifests: invalidManifests.length,
  missingSemanticFallbacks: missingSemanticFallbacks.length,
  suspiciousUntranslated: untranslated.length,
}, null, 2))

if (missing.length) console.error(`Missing English translations:\n${missing.join('\n')}`)
if (empty.length) console.error(`Empty English translations:\n${empty.join('\n')}`)
if (missingPluralForms.length) console.error(`Missing plural forms:\n${missingPluralForms.join('\n')}`)
if (invalidManifests.length) console.error(`Invalid locale manifests:\n${invalidManifests.join('\n')}`)
if (missingSemanticFallbacks.length) console.error(`Missing stable-key fallbacks:\n${missingSemanticFallbacks.join('\n')}`)
if (legacyKeys.length > maximumLegacyKeys) {
  console.error(`Legacy sentence keys increased to ${legacyKeys.length}; limit is ${maximumLegacyKeys}`)
}
if (untranslated.length) console.error(`Potential untranslated UI text:\n${untranslated.join('\n')}`)
if (
  missing.length || empty.length || missingPluralForms.length || invalidManifests.length ||
  missingSemanticFallbacks.length || legacyKeys.length > maximumLegacyKeys || untranslated.length
) process.exitCode = 1
