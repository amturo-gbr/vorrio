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

const customer = process.argv.find((argument) => argument.startsWith('--customer='))?.slice('--customer='.length)
assert.match(customer ?? '', /^cus_[A-Za-z0-9]+$/, 'Pass a Stripe test customer as --customer=cus_...')

const env = parseEnv(await readFile(ENV_PATH, 'utf8'))
const stripeKey = (env.get('STRIPE_RESTRICTED_KEY') ?? env.get('STRIPE_SECRET_KEY'))?.trim()
assert.equal(env.get('STRIPE_MODE'), 'test')
assertRestrictedKey('test', stripeKey)

const body = new URLSearchParams({
  customer,
  configuration: env.get('STRIPE_TEST_CUSTOMER_PORTAL_CONFIGURATION_ID'),
  return_url: 'https://vorrio.app/#unterstuetzen',
})
const response = await fetch(`${STRIPE_API}/billing_portal/sessions`, {
  method: 'POST',
  headers: {
    Authorization: `Bearer ${stripeKey}`,
    'Content-Type': 'application/x-www-form-urlencoded',
    'Stripe-Version': STRIPE_API_VERSION,
  },
  body,
})
const payload = await response.json()
if (!response.ok) throw new Error(payload?.error?.message ?? `Stripe returned HTTP ${response.status}`)
assert.equal(payload.livemode, false)
assert.match(payload.url ?? '', /^https:\/\/billing\.stripe\.com\/p\/session\/test_/)

console.log(payload.url)
