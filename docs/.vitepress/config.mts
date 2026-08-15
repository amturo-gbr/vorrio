import { defineConfig } from "vitepress";

const description =
  "Install, configure, operate and integrate Vorrio without access to a running household instance.";

export default defineConfig({
  lang: "en-US",
  title: "Vorrio Docs",
  titleTemplate: ":title · Vorrio Docs",
  description,
  appearance: false,
  cleanUrls: true,
  srcExclude: ["design/**"],
  sitemap: {
    hostname: "https://docs.vorrio.app",
  },
  markdown: {
    languageAlias: {
      env: "dotenv",
    },
  },
  head: [
    ["meta", { name: "theme-color", content: "#176b35" }],
    ["meta", { name: "author", content: "Amturo UG (haftungsbeschränkt)" }],
    ["meta", { name: "robots", content: "index, follow, max-image-preview:large" }],
    ["meta", { property: "og:type", content: "website" }],
    ["meta", { property: "og:site_name", content: "Vorrio Docs" }],
    ["meta", { property: "og:image", content: "https://docs.vorrio.app/vorrio-social-card-en.png" }],
    ["meta", { property: "og:image:width", content: "1200" }],
    ["meta", { property: "og:image:height", content: "630" }],
    ["meta", { name: "twitter:card", content: "summary_large_image" }],
    ["meta", { name: "twitter:image", content: "https://docs.vorrio.app/vorrio-social-card-en.png" }],
    ["link", { rel: "icon", type: "image/png", href: "/vorrio-icon.png" }],
    ["link", { rel: "apple-touch-icon", href: "/vorrio-icon.png" }],
  ],
  themeConfig: {
    logo: "/brand/vorrio-mark.png",
    siteTitle: "Vorrio Docs",
    nav: [
      { text: "Guide", link: "/" },
      { text: "API reference", link: "/api-reference" },
      { text: "GitHub", link: "https://github.com/amturo-gbr/vorrio" },
      { text: "vorrio.app", link: "https://vorrio.app" },
    ],
    search: {
      provider: "local",
      options: {
        translations: {
          button: {
            buttonText: "Search documentation",
            buttonAriaLabel: "Search documentation",
          },
          modal: {
            noResultsText: "No results found for",
            resetButtonTitle: "Clear search",
            footer: {
              selectText: "to select",
              navigateText: "to navigate",
              closeText: "to close",
            },
          },
        },
      },
    },
    sidebar: [
      {
        text: "Get started",
        items: [
          { text: "Overview", link: "/" },
          { text: "Getting started", link: "/GETTING-STARTED" },
          { text: "Installation", link: "/INSTALLATION" },
          { text: "Configuration", link: "/CONFIGURATION" },
          { text: "Daily workflow", link: "/WORKFLOW" },
        ],
      },
      {
        text: "Use Vorrio",
        items: [
          { text: "Barcode scanning", link: "/BARCODE-SCANNING" },
          { text: "Household budget", link: "/BUDGET" },
          { text: "Notifications", link: "/NOTIFICATIONS" },
          { text: "Mobile and PWA", link: "/MOBILE-APPS" },
          { text: "Migrate from Grocy", link: "/MIGRATION-GROCY" },
        ],
      },
      {
        text: "Operate safely",
        items: [
          { text: "Deployment profiles", link: "/DEPLOYMENT-PROFILES" },
          { text: "Identity and security", link: "/IDENTITY-SECURITY" },
          { text: "Backup and restore", link: "/BACKUP-RESTORE" },
          { text: "Data privacy", link: "/DATA-PRIVACY" },
          { text: "AI providers", link: "/AI-PROVIDERS" },
          { text: "Data sources", link: "/DATA-SOURCES" },
          { text: "Data model", link: "/DATA-MODEL" },
        ],
      },
      {
        text: "Develop and integrate",
        items: [
          { text: "API reference", link: "/api-reference" },
          { text: "REST API guide", link: "/API" },
          { text: "Automation tokens", link: "/AUTOMATION-TOKENS" },
          { text: "Localization", link: "/LOCALIZATION" },
          { text: "Translation community", link: "/TRANSLATION-COMMUNITY" },
        ],
      },
      {
        text: "Project",
        items: [
          { text: "Roadmap", link: "/ROADMAP" },
          { text: "Releases", link: "/RELEASES" },
          { text: "Governance", link: "/GOVERNANCE" },
          { text: "Funding", link: "/FUNDING" },
        ],
      },
    ],
    outline: {
      level: [2, 3],
      label: "On this page",
    },
    socialLinks: [{ icon: "github", link: "https://github.com/amturo-gbr/vorrio" }],
    editLink: {
      pattern: "https://github.com/amturo-gbr/vorrio/edit/main/docs/:path",
      text: "Edit this page on GitHub",
    },
    lastUpdated: {
      text: "Last updated",
      formatOptions: {
        dateStyle: "medium",
      },
    },
    docFooter: {
      prev: "Previous page",
      next: "Next page",
    },
    footer: {
      message: "Released under the AGPL-3.0-or-later license.",
      copyright: "© 2026 Amturo UG (haftungsbeschränkt)",
    },
  },
});
