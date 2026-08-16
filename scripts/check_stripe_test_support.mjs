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
assert.equal(env.get('STRIPE_MODE'), 'test')
assertRestrictedKey('test', stripeKey)

async function stripeGet(endpoint) {
  const response = await fetch(`${STRIPE_API}${endpoint}`, {
    headers: { Authorization: `Bearer ${stripeKey}`, 'Stripe-Version': STRIPE_API_VERSION },
  })
  const payload = await response.json()
  if (!response.ok) throw new Error(payload?.error?.message ?? `Stripe returned HTTP ${response.status}`)
  return payload
}

const definitions = [
  {
    prefix: 'STRIPE_TEST_ONE_TIME',
    productKey: 'one_time_v1',
    verifyPrice(price) {
      assert.equal(price.type, 'one_time')
      assert.equal(price.custom_unit_amount?.minimum, 200)
      assert.equal(price.custom_unit_amount?.preset, 1000)
    },
    verifyLink(link) {
      assert.equal(link.invoice_creation?.enabled, true)
    },
  },
  {
    prefix: 'STRIPE_TEST_MONTHLY_5',
    productKey: 'monthly_v1',
    verifyPrice(price) {
      assert.equal(price.unit_amount, 500)
      assert.equal(price.recurring?.interval, 'month')
    },
    verifyLink() {},
  },
  {
    prefix: 'STRIPE_TEST_MONTHLY_10',
    productKey: 'monthly_v1',
    verifyPrice(price) {
      assert.equal(price.unit_amount, 1000)
      assert.equal(price.recurring?.interval, 'month')
    },
    verifyLink() {},
  },
  {
    prefix: 'STRIPE_TEST_MONTHLY_25',
    productKey: 'monthly_v1',
    verifyPrice(price) {
      assert.equal(price.unit_amount, 2500)
      assert.equal(price.recurring?.interval, 'month')
    },
    verifyLink() {},
  },
]

for (const definition of definitions) {
  const product = await stripeGet(`/products/${env.get(`${definition.prefix}_PRODUCT_ID`)}`)
  const price = await stripeGet(`/prices/${env.get(`${definition.prefix}_PRICE_ID`)}`)
  const link = await stripeGet(`/payment_links/${env.get(`${definition.prefix}_PAYMENT_LINK_ID`)}`)

  for (const item of [product, price, link]) assert.equal(item.livemode, false)
  assert.equal(product.active, true)
  assert.equal(product.metadata?.vorrio_support_key, definition.productKey)
  assert.equal(product.metadata?.vorrio_environment, 'test')
  assert.equal(price.active, true)
  assert.equal(price.currency, 'eur')
  assert.equal(link.active, true)
  assert.equal(link.billing_address_collection, 'required')
  assert.equal(link.name_collection?.individual?.enabled, true)
  assert.equal(link.tax_id_collection?.enabled, true)
  assert.equal(link.payment_method_types, null)
  definition.verifyPrice(price)
  definition.verifyLink(link)

  const hostedPage = await fetch(env.get(`${definition.prefix}_PAYMENT_LINK_URL`))
  assert.equal(hostedPage.ok, true)
  assert.match(hostedPage.url, /^https:\/\/buy\.stripe\.com\/test_/)
}

const portal = await stripeGet(`/billing_portal/configurations/${env.get('STRIPE_TEST_CUSTOMER_PORTAL_CONFIGURATION_ID')}`)
assert.equal(portal.livemode, false)
assert.equal(portal.active, true)
assert.equal(portal.features?.invoice_history?.enabled, true)
assert.equal(portal.features?.payment_method_update?.enabled, true)
assert.equal(portal.features?.subscription_cancel?.enabled, true)
assert.equal(portal.features?.subscription_cancel?.mode, 'at_period_end')
assert.equal(portal.login_page?.enabled, true)
assert.match(portal.login_page?.url ?? '', /^https:\/\/billing\.stripe\.com\/p\/login\/test_/)

console.log('Stripe test support is healthy (4 hosted links, dynamic methods, invoices and customer portal).')
