self.addEventListener('push', (event) => {
  let message = {}
  try {
    message = event.data ? event.data.json() : {}
  } catch {
    message = { body: event.data ? event.data.text() : '' }
  }

  const locale = message.locale === 'en' ? 'en' : 'de'
  const title = message.title || 'Vorrio'
  const options = {
    body: message.body || (locale === 'en'
      ? 'There is an update about your stock.'
      : 'Es gibt Neuigkeiten zu deinem Vorrat.'),
    icon: '/pwa-icon.png',
    badge: '/pwa-icon.png',
    tag: message.tag || 'vorrio-notification',
    renotify: false,
    data: {
      url: message.url || '/',
      kind: message.kind || 'stock',
      locale,
    },
  }

  event.waitUntil(
    Promise.all([
      self.registration.showNotification(title, options),
      self.navigator?.setAppBadge ? self.navigator.setAppBadge(1) : Promise.resolve(),
    ]),
  )
})

self.addEventListener('notificationclick', (event) => {
  event.notification.close()
  const requested = new URL(event.notification.data?.url || '/', self.location.origin)
  const target = requested.origin === self.location.origin ? requested.href : self.location.origin
  event.waitUntil(
    self.clients.matchAll({ type: 'window', includeUncontrolled: true }).then(async (clients) => {
      if (self.navigator?.clearAppBadge) await self.navigator.clearAppBadge()
      for (const client of clients) {
        if ('navigate' in client) await client.navigate(target)
        if ('focus' in client) return client.focus()
      }
      return self.clients.openWindow ? self.clients.openWindow(target) : undefined
    }),
  )
})
