#!/usr/bin/env node

import { chmod, readFile, writeFile } from 'node:fs/promises'
import { fileURLToPath } from 'node:url'

const STRIPE_API = 'https://api.stripe.com/v1'
const STRIPE_API_VERSION = '2026-02-25.clover'
const ENV_PATH = fileURLToPath(new URL('../.env.stripe.local', import.meta.url))

function parseEnv(source) {
  const values = new Map()

  for (const line of source.split(/\r?\n/)) {
    if (!line || line.trimStart().startsWith('#')) continue
    const separator = line.indexOf('=')
    if (separator === -1) continue
    values.set(line.slice(0, separator), line.slice(separator + 1))
  }

  return values
}

function encode(entries) {
  const params = new URLSearchParams()
  for (const [key, value] of Object.entries(entries)) {
    if (Array.isArray(value)) {
      for (const item of value) params.append(key, String(item))
    } else {
      params.append(key, String(value))
    }
  }
  return params
}

const envSource = await readFile(ENV_PATH, 'utf8')
const env = parseEnv(envSource)
const stripeKey = env.get('STRIPE_SECRET_KEY')?.trim()

if (env.get('STRIPE_MODE') !== 'test' || !stripeKey?.startsWith('rk_test_')) {
  throw new Error('Refusing to run without a restricted Stripe test key')
}

async function stripeRequest(method, endpoint, entries = {}, idempotencyKey) {
  const params = encode(entries)
  const url = new URL(`${STRIPE_API}${endpoint}`)
  const headers = {
    Authorization: `Bearer ${stripeKey}`,
    'Stripe-Version': STRIPE_API_VERSION,
  }

  const options = { method, headers }
  if (method === 'GET') {
    url.search = params.toString()
  } else {
    headers['Content-Type'] = 'application/x-www-form-urlencoded'
    if (idempotencyKey) headers['Idempotency-Key'] = idempotencyKey
    options.body = params
  }

  const response = await fetch(url, options)
  const payload = await response.json()
  if (!response.ok) {
    const message = payload?.error?.message || `Stripe returned HTTP ${response.status}`
    throw new Error(`${method} ${endpoint} failed: ${message}`)
  }
  return payload
}

async function findOrCreateProduct(definition) {
  const products = await stripeRequest('GET', '/products', {
    active: true,
    limit: 100,
  })
  const existing = products.data.find(
    (product) => product.metadata?.vorrio_support_key === definition.key,
  )
  if (existing) return existing

  return stripeRequest(
    'POST',
    '/products',
    {
      name: definition.name,
      description: definition.description,
      'metadata[vorrio_support_key]': definition.key,
      'metadata[vorrio_project]': 'vorrio',
      'metadata[vorrio_environment]': 'test',
    },
    `vorrio-test-product-${definition.key}`,
  )
}

async function findOrCreatePrice(definition, product) {
  const prices = await stripeRequest('GET', '/prices', {
    active: true,
    limit: 100,
    product: product.id,
  })
  const existing = prices.data.find(
    (price) => price.metadata?.vorrio_support_key === definition.key,
  )
  if (existing) return existing

  const priceFields = definition.customAmount
    ? {
        'custom_unit_amount[enabled]': true,
        'custom_unit_amount[minimum]': definition.minimum,
        'custom_unit_amount[preset]': definition.preset,
      }
    : {
        unit_amount: definition.unitAmount,
        'recurring[interval]': 'month',
      }

  return stripeRequest(
    'POST',
    '/prices',
    {
      currency: 'eur',
      product: product.id,
      nickname: definition.nickname,
      lookup_key: `vorrio_support_${definition.key}_test`,
      'metadata[vorrio_support_key]': definition.key,
      'metadata[vorrio_project]': 'vorrio',
      'metadata[vorrio_environment]': 'test',
      ...priceFields,
    },
    `vorrio-test-price-${definition.key}`,
  )
}

async function configurePaymentLink(definition, price) {
  const links = await stripeRequest('GET', '/payment_links', {
    active: true,
    limit: 100,
  })
  let paymentLink = links.data.find(
    (link) => link.metadata?.vorrio_support_key === definition.key,
  )

  if (!paymentLink) {
    paymentLink = await stripeRequest(
      'POST',
      '/payment_links',
      {
        'line_items[0][price]': price.id,
        'line_items[0][quantity]': 1,
        'metadata[vorrio_support_key]': definition.key,
        'metadata[vorrio_project]': 'vorrio',
        'metadata[vorrio_environment]': 'test',
      },
      `vorrio-test-payment-link-${definition.key}-v2`,
    )
  }

  const invoiceFields = definition.customAmount
    ? {
        'invoice_creation[enabled]': true,
        'invoice_creation[invoice_data][description]':
          'Unterstützung für das Open-Source-Projekt Vorrio / Support for the Vorrio open-source project',
        'invoice_creation[invoice_data][footer]':
          'Keine steuerlich absetzbare Spende oder Spendenbescheinigung. / Not a tax-deductible donation or charitable donation receipt.',
      }
    : {}

  return stripeRequest('POST', `/payment_links/${paymentLink.id}`, {
    'after_completion[type]': 'hosted_confirmation',
    'after_completion[hosted_confirmation][custom_message]':
      'Danke für deine Unterstützung von Vorrio! / Thank you for supporting Vorrio!',
    billing_address_collection: 'required',
    'name_collection[individual][enabled]': true,
    'name_collection[individual][optional]': false,
    'name_collection[business][enabled]': true,
    'name_collection[business][optional]': true,
    'tax_id_collection[enabled]': true,
    'tax_id_collection[required]': 'never',
    'custom_text[submit][message]':
      'Unterstützung für Vorrio; keine steuerlich absetzbare Spende. / Support for Vorrio; not a tax-deductible donation.',
    'metadata[vorrio_support_key]': definition.key,
    'metadata[vorrio_project]': 'vorrio',
    'metadata[vorrio_environment]': 'test',
    ...invoiceFields,
  })
}

async function configureCustomerPortal() {
  const configurations = await stripeRequest('GET', '/billing_portal/configurations', {
    active: true,
    limit: 100,
  })
  let configuration = configurations.data.find(
    (item) => item.metadata?.vorrio_support_key === 'customer_portal_v1',
  )

  const fields = {
    name: 'Vorrio Support – Test',
    'business_profile[headline]':
      'Vorrio-Unterstützung verwalten / Manage Vorrio support',
    'features[customer_update][enabled]': true,
    'features[customer_update][allowed_updates][]': ['name', 'address', 'tax_id'],
    'features[invoice_history][enabled]': true,
    'features[payment_method_update][enabled]': true,
    'features[subscription_cancel][enabled]': true,
    'features[subscription_cancel][mode]': 'at_period_end',
    'features[subscription_cancel][proration_behavior]': 'none',
    'features[subscription_cancel][cancellation_reason][enabled]': true,
    'features[subscription_cancel][cancellation_reason][options][]': [
      'too_expensive',
      'unused',
      'other',
    ],
    'features[subscription_update][enabled]': false,
    'login_page[enabled]': true,
    'metadata[vorrio_support_key]': 'customer_portal_v1',
    'metadata[vorrio_project]': 'vorrio',
    'metadata[vorrio_environment]': 'test',
  }

  if (!configuration) {
    configuration = await stripeRequest(
      'POST',
      '/billing_portal/configurations',
      fields,
      'vorrio-test-customer-portal-v2',
    )
  } else {
    configuration = await stripeRequest(
      'POST',
      `/billing_portal/configurations/${configuration.id}`,
      { active: true, ...fields },
    )
  }

  if (
    configuration.livemode ||
    !configuration.active ||
    !configuration.features?.invoice_history?.enabled ||
    !configuration.features?.payment_method_update?.enabled ||
    !configuration.features?.subscription_cancel?.enabled ||
    configuration.features.subscription_cancel.mode !== 'at_period_end' ||
    !configuration.login_page?.enabled ||
    !configuration.login_page.url?.includes('/test_')
  ) {
    throw new Error('Unexpected Stripe test customer portal configuration')
  }

  return configuration
}

const definitions = [
  {
    key: 'one_time_v1',
    envPrefix: 'STRIPE_TEST_ONE_TIME',
    name: 'Vorrio Support – einmalig / one-time',
    description:
      'Frei wählbare Unterstützung für das Open-Source-Projekt Vorrio. / Flexible support for the Vorrio open-source project.',
    nickname: 'Vorrio flexible Unterstützung / flexible support',
    customAmount: true,
    minimum: 300,
    preset: 1000,
  },
  {
    key: 'monthly_v1',
    envPrefix: 'STRIPE_TEST_MONTHLY',
    name: 'Vorrio Support – monatlich / monthly',
    description:
      'Monatliche Unterstützung für das Open-Source-Projekt Vorrio. / Monthly support for the Vorrio open-source project.',
    nickname: 'Vorrio monatliche Unterstützung / monthly support',
    customAmount: false,
    unitAmount: 500,
  },
]

const results = []
for (const definition of definitions) {
  const product = await findOrCreateProduct(definition)
  const price = await findOrCreatePrice(definition, product)
  const paymentLink = await configurePaymentLink(definition, price)

  if (product.livemode || price.livemode || paymentLink.livemode) {
    throw new Error(`Refusing unexpected live Stripe object for ${definition.key}`)
  }
  if (!paymentLink.active) {
    throw new Error(`Payment Link is not active for ${definition.key}`)
  }
  if (definition.customAmount) {
    const customAmount = price.custom_unit_amount
    if (
      price.type !== 'one_time' ||
      customAmount?.minimum !== definition.minimum ||
      customAmount?.preset !== definition.preset ||
      !paymentLink.invoice_creation?.enabled
    ) {
      throw new Error(`Unexpected flexible price configuration for ${definition.key}`)
    }
  } else if (
    price.unit_amount !== definition.unitAmount ||
    price.recurring?.interval !== 'month'
  ) {
    throw new Error(`Unexpected monthly price configuration for ${definition.key}`)
  }

  if (
    paymentLink.billing_address_collection !== 'required' ||
    !paymentLink.name_collection?.individual?.enabled ||
    !paymentLink.tax_id_collection?.enabled ||
    paymentLink.payment_method_types !== null
  ) {
    throw new Error(`Unexpected checkout configuration for ${definition.key}`)
  }

  env.set(`${definition.envPrefix}_PRODUCT_ID`, product.id)
  env.set(`${definition.envPrefix}_PRICE_ID`, price.id)
  env.set(`${definition.envPrefix}_PAYMENT_LINK_ID`, paymentLink.id)
  env.set(`${definition.envPrefix}_PAYMENT_LINK_URL`, paymentLink.url)

  results.push({
    kind: definition.key,
    productId: product.id,
    priceId: price.id,
    paymentLinkId: paymentLink.id,
    url: paymentLink.url,
    pricing: definition.customAmount
      ? { currency: 'eur', minimum: definition.minimum, preset: definition.preset }
      : { currency: 'eur', unitAmount: definition.unitAmount, interval: 'month' },
  })
}

const portal = await configureCustomerPortal()
env.set('STRIPE_TEST_CUSTOMER_PORTAL_CONFIGURATION_ID', portal.id)
env.set('STRIPE_TEST_CUSTOMER_PORTAL_LOGIN_URL', portal.login_page.url)

const nextEnv = `${[...env.entries()].map(([key, value]) => `${key}=${value}`).join('\n')}\n`
await writeFile(ENV_PATH, nextEnv, { encoding: 'utf8', mode: 0o600 })
await chmod(ENV_PATH, 0o600)

console.log(
  JSON.stringify(
    {
      mode: 'test',
      results,
      customerPortal: {
        configurationId: portal.id,
        loginUrl: portal.login_page.url,
        invoiceHistory: portal.features.invoice_history.enabled,
        paymentMethodUpdate: portal.features.payment_method_update.enabled,
        subscriptionCancellation: portal.features.subscription_cancel.mode,
      },
    },
    null,
    2,
  ),
)
