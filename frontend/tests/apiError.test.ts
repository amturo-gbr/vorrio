import assert from 'node:assert/strict'
import test from 'node:test'
import { apiErrorMessage } from '../src/apiError.ts'
import { changeLocale } from '../src/i18n.ts'

test('API error formatter keeps normal server messages in German', async () => {
  await changeLocale('de')
  assert.equal(
    apiErrorMessage({ detail: 'Die Prüfziffer des Barcodes ist ungültig' }, 422),
    'Die Prüfziffer des Barcodes ist ungültig',
  )
})

test('API error formatter translates fixed and dynamic messages in English', async () => {
  await changeLocale('en')
  assert.equal(
    apiErrorMessage({ detail: 'Die Prüfziffer des Barcodes ist ungültig' }, 422),
    'The barcode check digit is invalid',
  )
  assert.equal(
    apiErrorMessage({ detail: 'Dem API-Token fehlt die Berechtigung scans:write' }, 403),
    'The API token is missing the scans:write permission',
  )
  await changeLocale('de')
})

test('API error formatter turns validation arrays into readable text', () => {
  assert.equal(
    apiErrorMessage({
      detail: [{ type: 'string_too_short', loc: ['body', 'barcode'], msg: 'String should have at least 4 characters' }],
    }, 422),
    'barcode: String should have at least 4 characters',
  )
})

test('API error formatter never renders an object directly', () => {
  assert.equal(apiErrorMessage({ detail: { unexpected: true } }, 500), 'HTTP 500')
})
