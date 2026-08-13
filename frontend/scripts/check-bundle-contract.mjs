import { readFile, stat } from 'node:fs/promises'
import { resolve } from 'node:path'

const frontendRoot = resolve(import.meta.dirname, '..')
const manifest = JSON.parse(await readFile(resolve(frontendRoot, 'dist/.vite/manifest.json'), 'utf8'))
const entry = manifest['index.html']

if (!entry?.file) {
  throw new Error('Vite manifest does not contain the index.html entry bundle')
}

const entryPath = resolve(frontendRoot, 'dist', entry.file)
const entryBytes = (await stat(entryPath)).size
const maximumEntryBytes = 500 * 1024

if (entryBytes > maximumEntryBytes) {
  throw new Error(`Initial JavaScript bundle is ${(entryBytes / 1024).toFixed(1)} KiB; limit is 500.0 KiB`)
}

if (manifest['src/locales/de/translation.json']) {
  throw new Error('the German fallback catalog must remain embedded in the entry bundle')
}

for (const locale of ['en']) {
  const localeSource = `src/locales/${locale}/translation.json`
  const localeEntry = manifest[localeSource]
  if (!localeEntry?.isDynamicEntry || !localeEntry.file) {
    throw new Error(`${localeSource} must build as a separate lazy language chunk`)
  }
  if (!entry.dynamicImports?.includes(localeSource)) {
    throw new Error(`index.html must reference ${localeSource} as a dynamic import`)
  }
  if (entry.imports?.includes(localeSource)) {
    throw new Error(`${localeSource} must not be a static entry dependency`)
  }
}

console.log(`Initial JavaScript bundle: ${(entryBytes / 1024).toFixed(1)} KiB (limit 500.0 KiB)`)
