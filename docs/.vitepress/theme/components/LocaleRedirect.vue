<script setup lang="ts">
import { onMounted, ref } from "vue";

const STORAGE_KEY = "vorrio-docs-locale";
const redirecting = ref(false);

function selectLocale(locale: "de" | "en") {
  localStorage.setItem(STORAGE_KEY, locale);
  window.location.replace(`/${locale}/`);
}

onMounted(() => {
  const stored = localStorage.getItem(STORAGE_KEY);
  const locale = stored === "de" || stored === "en"
    ? stored
    : navigator.languages.some((language) => language.toLowerCase().startsWith("de")) ? "de" : "en";
  redirecting.value = true;
  selectLocale(locale);
});
</script>

<template>
  <main class="locale-gateway">
    <img src="/brand/vorrio-mark.png" alt="" width="56" height="56" />
    <p class="locale-brand">Vorrio Docs</p>
    <h1>Sprache wählen · Choose language</h1>
    <p>Dokumentation auf Deutsch oder Englisch öffnen.</p>
    <p>Open the documentation in German or English.</p>
    <div class="locale-actions">
      <a href="/de/" lang="de" @click.prevent="selectLocale('de')">Deutsch</a>
      <a href="/en/" lang="en" @click.prevent="selectLocale('en')">English</a>
    </div>
    <p v-if="redirecting" class="locale-status" aria-live="polite">Weiterleitung · Redirecting…</p>
  </main>
</template>

