const menuButton = document.querySelector('[data-menu-button]')
const siteNav = document.querySelector('[data-site-nav]')
const siteHeader = document.querySelector('[data-site-header]')

function closeMenu() {
  if (!menuButton || !siteNav) return
  menuButton.setAttribute('aria-expanded', 'false')
  siteNav.classList.remove('open')
  document.body.classList.remove('menu-open')
}

menuButton?.addEventListener('click', () => {
  const open = menuButton.getAttribute('aria-expanded') !== 'true'
  menuButton.setAttribute('aria-expanded', String(open))
  siteNav?.classList.toggle('open', open)
  document.body.classList.toggle('menu-open', open)
})

siteNav?.querySelectorAll('a').forEach((link) => link.addEventListener('click', closeMenu))

window.addEventListener('resize', () => {
  if (window.innerWidth > 900) closeMenu()
})

function updateHeader() {
  siteHeader?.classList.toggle('scrolled', window.scrollY > 8)
}

window.addEventListener('scroll', updateHeader, { passive: true })
updateHeader()

document.querySelectorAll('[data-privacy-settings]').forEach((button) => {
  button.addEventListener('click', () => {
    window.__ucCmp?.showSecondLayer()
  })
})

const revealObserver = new IntersectionObserver(
  (entries) => {
    entries.forEach((entry) => {
      if (!entry.isIntersecting) return
      entry.target.classList.add('visible')
      revealObserver.unobserve(entry.target)
    })
  },
  { rootMargin: '0px 0px -8% 0px', threshold: 0.08 },
)

document.querySelectorAll('.reveal').forEach((element) => revealObserver.observe(element))

const copyButton = document.querySelector('[data-copy-command]')
const copyLabels = document.documentElement.lang === 'en'
  ? { idle: 'Copy', copied: 'Copied', failed: 'Unavailable' }
  : { idle: 'Kopieren', copied: 'Kopiert', failed: 'Nicht möglich' }
const installCommand = `git clone https://github.com/amturo-gbr/vorrio.git
cd vorrio
cp .env.example .env
docker compose up -d --build`

copyButton?.addEventListener('click', async () => {
  try {
    await navigator.clipboard.writeText(installCommand)
    copyButton.textContent = copyLabels.copied
    window.setTimeout(() => {
      copyButton.textContent = copyLabels.idle
    }, 1800)
  } catch {
    copyButton.textContent = copyLabels.failed
  }
})
