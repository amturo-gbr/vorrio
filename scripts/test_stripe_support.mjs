import assert from 'node:assert/strict'
import { readFile } from 'node:fs/promises'
import test from 'node:test'
import {
  STRIPE_API_VERSION,
  assertRestrictedKey,
  liveAccountReadiness,
  missingLiveApprovals,
} from './stripe_support_contract.mjs'

const readyAccount = {
  id: 'acct_expected',
  object: 'account',
  details_submitted: true,
  charges_enabled: true,
  payouts_enabled: true,
  default_currency: 'eur',
  requirements: { currently_due: [], past_due: [], pending_verification: [] },
  business_profile: { support_email: 'support@example.test', support_url: 'https://example.test/support' },
  settings: {
    branding: { logo: 'file_logo', icon: null, primary_color: '#176b35' },
    payments: { statement_descriptor: 'AMTURO.DE' },
    payouts: { schedule: { interval: 'daily' } },
  },
  external_accounts: { data: [{ status: 'verified' }] },
}

test('Stripe contract uses the current API version', () => {
  assert.equal(STRIPE_API_VERSION, '2026-06-24.dahlia')
})

test('ready live account passes without blockers', () => {
  assert.deepEqual(liveAccountReadiness(readyAccount, 'acct_expected'), { blockers: [], warnings: [] })
})

test('live preflight reports missing public profile and branding', () => {
  const account = structuredClone(readyAccount)
  account.business_profile.support_email = null
  account.business_profile.support_url = null
  account.settings.branding = { logo: null, icon: null, primary_color: null }
  const { blockers } = liveAccountReadiness(account, 'acct_expected')
  assert.deepEqual(blockers, [
    'public support email is missing',
    'public support URL is missing',
    'Stripe Checkout branding logo or icon is missing',
    'Stripe Checkout brand colour is missing',
  ])
})

test('live preflight keeps the shared account descriptor on Amturo', () => {
  const account = structuredClone(readyAccount)
  account.settings.payments.statement_descriptor = 'VORRIO'
  assert.deepEqual(liveAccountReadiness(account, 'acct_expected').blockers, [
    'statement descriptor must identify Amturo',
  ])
})

test('live writes require every independent approval gate', () => {
  const env = new Map([
    ['STRIPE_LEGAL_COPY_APPROVED', 'YES'],
    ['STRIPE_TAX_REVIEW_APPROVED', 'NO'],
    ['STRIPE_BOOKKEEPING_APPROVED', 'YES'],
  ])
  assert.deepEqual(missingLiveApprovals(env), ['STRIPE_TAX_REVIEW_APPROVED'])
})

test('restricted keys cannot be mixed between environments', () => {
  assert.doesNotThrow(() => assertRestrictedKey('test', 'rk_test_example'))
  assert.doesNotThrow(() => assertRestrictedKey('live', 'rk_live_example'))
  assert.throws(() => assertRestrictedKey('live', 'sk_live_example'))
  assert.throws(() => assertRestrictedKey('live', 'rk_test_example'))
})

test('setup never hard-codes payment method types or automatic tax', async () => {
  const source = await readFile(new URL('./setup_stripe_support.mjs', import.meta.url), 'utf8')
  assert.doesNotMatch(source, /['"]payment_method_types(?:\[[^\]]+\])?['"]\s*:/)
  assert.doesNotMatch(source, /automatic_tax/)
  assert.match(source, /paymentLink\.payment_method_types !== null/)
})

test('support setup defines the approved one-time and monthly test prices', async () => {
  const source = await readFile(new URL('./setup_stripe_support.mjs', import.meta.url), 'utf8')
  assert.match(source, /key: 'one_time_v2'[\s\S]*?minimum: 200,[\s\S]*?preset: 1000,/)
  assert.match(source, /key: 'monthly_v1'[\s\S]*?unitAmount: 500,/)
  assert.match(source, /key: 'monthly_10_v1'[\s\S]*?unitAmount: 1000,/)
  assert.match(source, /key: 'monthly_25_v1'[\s\S]*?unitAmount: 2500,/)
})
