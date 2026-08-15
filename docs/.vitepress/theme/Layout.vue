<script setup lang="ts">
import DefaultTheme from "vitepress/theme";
import { inBrowser, useData, useRoute } from "vitepress";
import { nextTick, onMounted, watch } from "vue";

const { lang } = useData();
const route = useRoute();

async function applyLocale() {
  if (!inBrowser) return;
  const locale = route.path.startsWith("/de/") ? "de" : route.path.startsWith("/en/") ? "en" : null;
  if (locale) localStorage.setItem("vorrio-docs-locale", locale);
  document.documentElement.lang = lang.value;
  await nextTick();
  requestAnimationFrame(() => {
    const german = locale === "de";
    document.querySelectorAll<HTMLButtonElement>("button.copy").forEach((button) => {
      const label = german ? "Code kopieren" : "Copy code";
      button.title = label;
      button.setAttribute("aria-label", label);
    });
    document.querySelectorAll<HTMLAnchorElement>("a.header-anchor").forEach((anchor) => {
      const heading = anchor.parentElement?.textContent?.replace("#", "").trim() ?? "";
      anchor.setAttribute("aria-label", german ? `Direktlink zu „${heading}“` : `Permalink to “${heading}”`);
    });
  });
}

onMounted(() => void applyLocale());
watch(() => route.path, () => void applyLocale());
</script>

<template>
  <DefaultTheme.Layout />
</template>
