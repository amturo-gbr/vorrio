#!/usr/bin/env node

import assert from 'node:assert/strict'
import { readFile } from 'node:fs/promises'
import { fileURLToPath } from 'node:url'
import { STRIPE_API_VERSION, assertRestrictedKey } from './stripe_support_contract.mjs'

const STRIPE_API = 'https://api.stripe.com/v1'
const ENV_PATH = fileURLToPath(new URL('../.env.stripe.local', import.meta.url))

function parseEnv(source) {
  return new Map(
    source.split(/\r?\n/)
      .filter((line) => line && !line.trimStart().startsWith('#') && line.includes('='))
      .map((line) => [line.slice(0, line.indexOf('=')), line.slice(line.indexOf('=') + 1)]),
  )
}

const env = parseEnv(await readFile(ENV_PATH, 'utf8'))
const stripeKey = (env.get('STRIPE_RESTRICTED_KEY') ?? env.get('STRIPE_SECRET_KEY'))?.trim()
const sessionsOnly = process.argv.includes('--sessions-only')
assert.equal(env.get('STRIPE_MODE'), 'test')
assertRestrictedKey('test', stripeKey)

async function stripeGet(endpoint, parameters = {}) {
  const url = new URL(`${STRIPE_API}${endpoint}`)
  for (const [key, value] of Object.entries(parameters)) url.searchParams.set(key, value)
  const response = await fetch(url, {
    headers: { Authorization: `Bearer ${stripeKey}`, 'Stripe-Version': STRIPE_API_VERSION },
  })
  const payload = await response.json()
  if (!response.ok) throw new Error(payload?.error?.message ?? `Stripe returned HTTP ${response.status}`)
  return payload
}

const expected = [
  {
    email: 'vorrio-sandbox-one-time@example.com',
    mode: 'payment',
    amount: 1000,
    paymentLinkId: env.get('STRIPE_TEST_ONE_TIME_PAYMENT_LINK_ID'),
  },
  {
    email: 'vorrio-sandbox-monthly-5@example.com',
    mode: 'subscription',
    amount: 500,
    paymentLinkId: env.get('STRIPE_TEST_MONTHLY_5_PAYMENT_LINK_ID'),
  },
  {
    email: 'vorrio-sandbox-monthly-10@example.com',
    mode: 'subscription',
    amount: 1000,
    paymentLinkId: env.get('STRIPE_TEST_MONTHLY_10_PAYMENT_LINK_ID'),
  },
  {
    email: 'vorrio-sandbox-monthly-25@example.com',
    mode: 'subscription',
    amount: 2500,
    paymentLinkId: env.get('STRIPE_TEST_MONTHLY_25_PAYMENT_LINK_ID'),
  },
]

const sessions = await stripeGet('/checkout/sessions', { limit: '100', status: 'complete' })
const results = []

for (const item of expected) {
  const session = sessions.data.find(
    (candidate) => candidate.customer_details?.email === item.email && candidate.payment_link === item.paymentLinkId,
  )
  assert.ok(session, `Missing completed Checkout Session for ${item.email}`)
  assert.equal(session.livemode, false)
  assert.equal(session.mode, item.mode)
  assert.equal(session.status, 'complete')
  assert.equal(session.payment_status, 'paid')
  assert.equal(session.currency, 'eur')
  assert.equal(session.amount_total, item.amount)

  if (item.mode === 'payment') {
    assert.ok(session.payment_intent)
    assert.ok(session.invoice)
    if (sessionsOnly) {
      results.push({ kind: 'one-time', session })
      continue
    }
    const invoice = await stripeGet(`/invoices/${session.invoice}`)
    assert.equal(invoice.livemode, false)
    assert.equal(invoice.status, 'paid')
    assert.equal(invoice.amount_paid, item.amount)
    results.push({ kind: 'one-time', session, invoice })
    continue
  }

  assert.ok(session.customer)
  assert.ok(session.subscription)
  if (sessionsOnly) {
    results.push({ kind: 'monthly', session })
    continue
  }
  const subscription = await stripeGet(`/subscriptions/${session.subscription}`)
  assert.equal(subscription.livemode, false)
  assert.equal(subscription.status, 'active')
  const invoice = await stripeGet(`/invoices/${subscription.latest_invoice}`)
  assert.equal(invoice.livemode, false)
  assert.equal(invoice.status, 'paid')
  assert.equal(invoice.amount_paid, item.amount)
  results.push({ kind: 'monthly', session, subscription, invoice })
}

if (sessionsOnly) {
  console.log('Stripe Sandbox Checkout Sessions are healthy (1 paid one-time payment and 3 paid subscription checkouts).')
} else {
  console.log(
    `Stripe Sandbox transactions are healthy (${results.filter((item) => item.kind === 'one-time').length} one-time payment, ${results.filter((item) => item.kind === 'monthly').length} active subscriptions, 4 paid invoices).`,
  )
}
