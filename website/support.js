(() => {
  const links = window.VORRIO_SUPPORT_LINKS
  if (!links) return

  const allowedHosts = new Set(['buy.stripe.com', 'billing.stripe.com'])

  document.querySelectorAll('[data-support-link]').forEach((link) => {
    const value = links[link.dataset.supportLink]

    try {
      const url = new URL(value)
      if (url.protocol !== 'https:' || !allowedHosts.has(url.hostname)) throw new Error('invalid host')
      link.href = url.href
    } catch {
      link.hidden = true
    }
  })
})()
