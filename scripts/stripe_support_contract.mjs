export const STRIPE_API_VERSION = '2026-06-24.dahlia'

export const LIVE_APPROVAL_KEYS = [
  'STRIPE_LEGAL_COPY_APPROVED',
  'STRIPE_TAX_REVIEW_APPROVED',
  'STRIPE_BOOKKEEPING_APPROVED',
]

export function liveAccountReadiness(account, expectedAccountId) {
  const blockers = []
  const warnings = []

  if (!account || account.object !== 'account') blockers.push('Stripe account could not be read')
  if (expectedAccountId && account?.id !== expectedAccountId) blockers.push('Stripe account ID does not match')
  if (!account?.details_submitted) blockers.push('business verification details are incomplete')
  if (!account?.charges_enabled) blockers.push('live charges are not enabled')
  if (!account?.payouts_enabled) blockers.push('payouts are not enabled')

  for (const field of ['currently_due', 'past_due', 'pending_verification']) {
    if (account?.requirements?.[field]?.length) blockers.push(`account requirements ${field.replaceAll('_', ' ')}`)
  }

  if (!account?.business_profile?.support_email) blockers.push('public support email is missing')
  if (!account?.business_profile?.support_url) blockers.push('public support URL is missing')
  if (!account?.settings?.branding?.logo && !account?.settings?.branding?.icon) {
    blockers.push('Stripe Checkout branding logo or icon is missing')
  }
  if (!account?.settings?.branding?.primary_color) blockers.push('Stripe Checkout brand colour is missing')

  const descriptor = account?.settings?.payments?.statement_descriptor ?? ''
  if (!/AMTURO/i.test(descriptor)) blockers.push('statement descriptor must identify Amturo')
  if (account?.default_currency !== 'eur') blockers.push('default currency must be EUR')

  if (account?.settings?.payouts?.schedule?.interval === 'manual') {
    warnings.push('payout schedule is manual; confirm this is intentional for bookkeeping')
  }
  if (account?.external_accounts?.data?.some((item) => item.status && item.status !== 'verified')) {
    warnings.push('review payout bank-account status in the Stripe Dashboard')
  }

  return { blockers, warnings }
}

export function missingLiveApprovals(env) {
  return LIVE_APPROVAL_KEYS.filter((key) => env.get(key) !== 'YES')
}

export function assertRestrictedKey(mode, key) {
  const prefix = mode === 'live' ? 'rk_live_' : 'rk_test_'
  if (!key?.startsWith(prefix)) {
    throw new Error(`Refusing ${mode} setup without a restricted ${prefix} key`)
  }
}
