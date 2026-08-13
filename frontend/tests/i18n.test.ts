import assert from 'node:assert/strict'
import test from 'node:test'
import {
  changeLocale,
  currentLocale,
  formatNumber,
  localeManifest,
  resolveLocale,
  supportedLocales,
  translate,
} from '../src/i18n.ts'

test('locale resolution supports German and English regional browser values', () => {
  assert.equal(resolveLocale('de-DE'), 'de')
  assert.equal(resolveLocale('en-GB'), 'en')
  assert.equal(resolveLocale('fr-FR'), 'de')
})

test('the language registry exposes reviewed native labels and metadata', () => {
  assert.deepEqual(supportedLocales, ['de', 'en'])
  assert.equal(localeManifest('de').native_name, 'Deutsch')
  assert.equal(localeManifest('en').native_name, 'English')
  assert.equal(localeManifest('de').tier, 'official')
  assert.equal(localeManifest('en').completion, 100)
})

test('language changes update translations and locale-aware number formatting', async () => {
  await changeLocale('de')
  assert.equal(currentLocale(), 'de')
  assert.equal(translate('Einstellungen'), 'Einstellungen')
  assert.equal(translate('{{count}} Produkte', { count: 1 }), '1 Produkt')
  assert.equal(translate('{{count}} Produkte', { count: 2 }), '2 Produkte')
  assert.equal(formatNumber(1234.5), '1.234,5')

  await changeLocale('en')
  assert.equal(currentLocale(), 'en')
  assert.equal(translate('Einstellungen'), 'Settings')
  assert.equal(translate('{{count}} Produkte', { count: 1 }), '1 product')
  assert.equal(translate('{{count}} Produkte', { count: 2 }), '2 products')
  assert.equal(formatNumber(1234.5), '1,234.5')

  await changeLocale('de')
})
