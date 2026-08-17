import { defineConfig, type DefaultTheme, type HeadConfig } from "vitepress";

const origin = "https://docs.vorrio.app";
const repository = "https://github.com/amturo-gbr/vorrio";

const deSidebar: DefaultTheme.SidebarItem[] = [
  {
    text: "Erste Schritte",
    items: [
      { text: "Überblick", link: "/de/" },
      { text: "Erste Schritte", link: "/de/GETTING-STARTED" },
      { text: "Installation", link: "/de/INSTALLATION" },
      { text: "Konfiguration", link: "/de/CONFIGURATION" },
      { text: "Alltäglicher Ablauf", link: "/de/WORKFLOW" },
    ],
  },
  {
    text: "Vorrio verwenden",
    items: [
      { text: "Produkte scannen", link: "/de/BARCODE-SCANNING" },
      { text: "Haushaltsbudget", link: "/de/BUDGET" },
      { text: "Benachrichtigungen", link: "/de/NOTIFICATIONS" },
      { text: "Mobil und als PWA", link: "/de/MOBILE-APPS" },
      { text: "Von Grocy migrieren", link: "/de/MIGRATION-GROCY" },
    ],
  },
  {
    text: "Sicher betreiben",
    items: [
      { text: "Bereitstellungsprofile", link: "/de/DEPLOYMENT-PROFILES" },
      { text: "Identität und Sicherheit", link: "/de/IDENTITY-SECURITY" },
      { text: "Sichern und wiederherstellen", link: "/de/BACKUP-RESTORE" },
      { text: "Datenschutz", link: "/de/DATA-PRIVACY" },
      { text: "KI-Anbieter", link: "/de/AI-PROVIDERS" },
      { text: "Datenquellen", link: "/de/DATA-SOURCES" },
      { text: "Datenmodell", link: "/de/DATA-MODEL" },
    ],
  },
  {
    text: "Entwickeln und integrieren",
    items: [
      { text: "API-Referenz", link: "/de/api-reference" },
      { text: "REST-API-Anleitung", link: "/de/API" },
      { text: "Automatisierungs-Tokens", link: "/de/AUTOMATION-TOKENS" },
      { text: "Lokalisierung", link: "/de/LOCALIZATION" },
      { text: "Übersetzungs-Community", link: "/de/TRANSLATION-COMMUNITY" },
    ],
  },
  {
    text: "Projekt",
    items: [
      { text: "Roadmap", link: "/de/ROADMAP" },
      { text: "Versionen", link: "/de/RELEASES" },
      { text: "Governance", link: "/de/GOVERNANCE" },
    ],
  },
];

const enSidebar: DefaultTheme.SidebarItem[] = [
  {
    text: "Get started",
    items: [
      { text: "Overview", link: "/en/" },
      { text: "Getting started", link: "/en/GETTING-STARTED" },
      { text: "Installation", link: "/en/INSTALLATION" },
      { text: "Configuration", link: "/en/CONFIGURATION" },
      { text: "Daily workflow", link: "/en/WORKFLOW" },
    ],
  },
  {
    text: "Use Vorrio",
    items: [
      { text: "Barcode scanning", link: "/en/BARCODE-SCANNING" },
      { text: "Household budget", link: "/en/BUDGET" },
      { text: "Notifications", link: "/en/NOTIFICATIONS" },
      { text: "Mobile and PWA", link: "/en/MOBILE-APPS" },
      { text: "Migrate from Grocy", link: "/en/MIGRATION-GROCY" },
    ],
  },
  {
    text: "Operate safely",
    items: [
      { text: "Deployment profiles", link: "/en/DEPLOYMENT-PROFILES" },
      { text: "Identity and security", link: "/en/IDENTITY-SECURITY" },
      { text: "Backup and restore", link: "/en/BACKUP-RESTORE" },
      { text: "Data privacy", link: "/en/DATA-PRIVACY" },
      { text: "AI providers", link: "/en/AI-PROVIDERS" },
      { text: "Data sources", link: "/en/DATA-SOURCES" },
      { text: "Data model", link: "/en/DATA-MODEL" },
    ],
  },
  {
    text: "Develop and integrate",
    items: [
      { text: "API reference", link: "/en/api-reference" },
      { text: "REST API guide", link: "/en/API" },
      { text: "Automation tokens", link: "/en/AUTOMATION-TOKENS" },
      { text: "Localization", link: "/en/LOCALIZATION" },
      { text: "Translation community", link: "/en/TRANSLATION-COMMUNITY" },
    ],
  },
  {
    text: "Project",
    items: [
      { text: "Roadmap", link: "/en/ROADMAP" },
      { text: "Releases", link: "/en/RELEASES" },
      { text: "Governance", link: "/en/GOVERNANCE" },
    ],
  },
];

const localeTheme = (locale: "de" | "en"): DefaultTheme.Config => {
  const de = locale === "de";
  return {
    nav: [
      { text: de ? "Anleitung" : "Guide", link: `/${locale}/` },
      { text: de ? "API-Referenz" : "API reference", link: `/${locale}/api-reference` },
      { text: "GitHub", link: repository },
      { text: "vorrio.app", link: "https://vorrio.app" },
    ],
    sidebar: de ? deSidebar : enSidebar,
    outline: { level: [2, 3], label: de ? "Auf dieser Seite" : "On this page" },
    editLink: {
      pattern: `${repository}/edit/main/docs/:path`,
      text: de ? "Diese Seite auf GitHub bearbeiten" : "Edit this page on GitHub",
    },
    lastUpdated: {
      text: de ? "Zuletzt aktualisiert" : "Last updated",
      formatOptions: { dateStyle: "medium", forceLocale: true },
    },
    docFooter: {
      prev: de ? "Vorherige Seite" : "Previous page",
      next: de ? "Nächste Seite" : "Next page",
    },
    footer: {
      message: de ? "Veröffentlicht unter der Lizenz AGPL-3.0-or-later." : "Released under the AGPL-3.0-or-later license.",
      copyright: "© 2026 Amturo UG (haftungsbeschränkt)",
    },
    sidebarMenuLabel: de ? "Menü" : "Menu",
    returnToTopLabel: de ? "Nach oben" : "Return to top",
    langMenuLabel: de ? "Sprache ändern" : "Change language",
  };
};

const searchTranslations = (de: boolean) => ({
  button: {
    buttonText: de ? "Dokumentation durchsuchen" : "Search documentation",
    buttonAriaLabel: de ? "Dokumentation durchsuchen" : "Search documentation",
  },
  modal: {
    displayDetails: de ? "Detaillierte Treffer anzeigen" : "Display detailed list",
    resetButtonTitle: de ? "Suche zurücksetzen" : "Clear search",
    backButtonTitle: de ? "Suche schließen" : "Close search",
    noResultsText: de ? "Keine Ergebnisse gefunden für" : "No results found for",
    footer: {
      selectText: de ? "auswählen" : "to select",
      selectKeyAriaLabel: "Enter",
      navigateText: de ? "navigieren" : "to navigate",
      navigateUpKeyAriaLabel: de ? "Pfeil nach oben" : "Arrow up",
      navigateDownKeyAriaLabel: de ? "Pfeil nach unten" : "Arrow down",
      closeText: de ? "schließen" : "to close",
      closeKeyAriaLabel: "Escape",
    },
  },
});

function pageUrl(locale: "de" | "en", relativePage: string) {
  const route = relativePage.replace(/index\.md$/, "").replace(/\.md$/, "");
  return `${origin}/${locale}/${route}`;
}

function localizedHead(page: string): HeadConfig[] {
  if (page === "404.md") return [];
  const match = page.match(/^(de|en)\/(.*)$/);
  if (!match) {
    return [
      ["link", { rel: "canonical", href: `${origin}/` }],
      ["link", { rel: "alternate", hreflang: "de", href: `${origin}/de/` }],
      ["link", { rel: "alternate", hreflang: "en", href: `${origin}/en/` }],
      ["link", { rel: "alternate", hreflang: "x-default", href: `${origin}/` }],
    ];
  }
  const locale = match[1] as "de" | "en";
  const relativePage = match[2];
  return [
    ["link", { rel: "canonical", href: pageUrl(locale, relativePage) }],
    ["link", { rel: "alternate", hreflang: "de", href: pageUrl("de", relativePage) }],
    ["link", { rel: "alternate", hreflang: "en", href: pageUrl("en", relativePage) }],
    ["link", { rel: "alternate", hreflang: "x-default", href: pageUrl("en", relativePage) }],
  ];
}

export default defineConfig({
  lang: "en-US",
  title: "Vorrio Docs",
  titleTemplate: ":title · Vorrio Docs",
  description: "Install, configure, operate and integrate Vorrio without access to a running household instance.",
  appearance: false,
  cleanUrls: true,
  srcExclude: ["design/**"],
  sitemap: { hostname: origin },
  markdown: { languageAlias: { env: "dotenv" } },
  locales: {
    de: {
      label: "Deutsch",
      lang: "de-DE",
      link: "/de/",
      title: "Vorrio Docs",
      description: "Vorrio installieren, konfigurieren, sicher betreiben und integrieren – ohne Zugriff auf eine laufende Haushaltsinstanz.",
      themeConfig: localeTheme("de"),
      markdown: {
        container: { tipLabel: "Tipp", warningLabel: "Warnung", dangerLabel: "Gefahr", infoLabel: "Information", detailsLabel: "Details" },
        codeCopyButton: { tooltipText: "Code kopieren", copiedText: "Kopiert" },
      },
    },
    en: {
      label: "English",
      lang: "en-US",
      link: "/en/",
      title: "Vorrio Docs",
      description: "Install, configure, operate and integrate Vorrio without access to a running household instance.",
      themeConfig: localeTheme("en"),
    },
  },
  head: [
    ["meta", { name: "theme-color", content: "#176b35" }],
    ["meta", { name: "author", content: "Amturo UG (haftungsbeschränkt)" }],
    ["meta", { name: "robots", content: "index, follow, max-image-preview:large" }],
    ["meta", { property: "og:type", content: "website" }],
    ["meta", { property: "og:site_name", content: "Vorrio Docs" }],
    ["meta", { property: "og:image", content: `${origin}/vorrio-social-card.png` }],
    ["meta", { property: "og:image:width", content: "1200" }],
    ["meta", { property: "og:image:height", content: "630" }],
    ["meta", { name: "twitter:card", content: "summary_large_image" }],
    ["meta", { name: "twitter:image", content: `${origin}/vorrio-social-card.png` }],
    ["link", { rel: "icon", type: "image/png", href: "/vorrio-icon.png" }],
    ["link", { rel: "apple-touch-icon", href: "/vorrio-icon.png" }],
  ],
  transformHead({ page }) {
    return localizedHead(page);
  },
  themeConfig: {
    logo: "/brand/vorrio-mark.png",
    siteTitle: "Vorrio Docs",
    socialLinks: [{ icon: "github", link: repository }],
    search: {
      provider: "local",
      options: {
        locales: {
          de: { translations: searchTranslations(true) },
          en: { translations: searchTranslations(false) },
        },
      },
    },
  },
});
