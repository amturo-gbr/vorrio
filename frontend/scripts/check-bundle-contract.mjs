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

console.log(`Initial JavaScript bundle: ${(entryBytes / 1024).toFixed(1)} KiB (limit 500.0 KiB)`)
