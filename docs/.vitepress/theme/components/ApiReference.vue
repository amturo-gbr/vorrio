<script setup lang="ts">
import { computed, ref } from "vue";
import { useData } from "vitepress";
import specification from "../../../api/openapi.json";
import germanApi from "../../../api/openapi.de.json";

type HttpMethod = "get" | "post" | "put" | "patch" | "delete";
type OpenApiOperation = {
  tags?: string[];
  summary?: string;
  description?: string;
  operationId?: string;
  deprecated?: boolean;
  security?: Array<Record<string, string[]>>;
};

type Operation = {
  method: HttpMethod;
  path: string;
  tag: string;
  summary: string;
  description: string;
  operationId: string;
  deprecated: boolean;
  authenticated: boolean;
};

const methods = new Set<HttpMethod>(["get", "post", "put", "patch", "delete"]);
const { lang } = useData();
const isGerman = computed(() => lang.value.toLowerCase().startsWith("de"));
const copy = computed(() => isGerman.value ? {
  heading: "REST-API erkunden",
  intro: "Durchsuche den eingecheckten öffentlichen Vertrag, ohne eine Verbindung zu einem Haushalt herzustellen. Von dieser Dokumentationsseite werden keine Anfragen ausgeführt.",
  download: "OpenAPI-JSON herunterladen",
  filterLabel: "Endpunkte filtern",
  filterPlaceholder: "Nach Pfad, Methode oder Zusammenfassung filtern",
  group: "Gruppe",
  all: "Alle",
  operations: "Operationen",
  fallback: "Diese Operation ist im kanonischen Vorrio-OpenAPI-Vertrag definiert.",
  operationId: "Operations-ID",
  authentication: "Authentifizierung",
  authenticated: "Sitzung oder unterstütztes Bearer-Token mit eingeschränktem Umfang",
  unauthenticated: "Keine Anforderung auf Operationsebene",
  status: "Status",
  deprecated: "Veraltet",
  empty: "Keine Endpunkte entsprechen diesem Filter.",
} : {
  heading: "Explore the REST API",
  intro: "Browse the checked-in public contract without connecting to a household. Requests are not executed from this documentation site.",
  download: "Download OpenAPI JSON",
  filterLabel: "Filter endpoints",
  filterPlaceholder: "Filter by path, method or summary",
  group: "Group",
  all: "All",
  operations: "operations",
  fallback: "This operation is defined in the canonical Vorrio OpenAPI contract.",
  operationId: "Operation ID",
  authentication: "Authentication",
  authenticated: "Session or supported scoped bearer token",
  unauthenticated: "No operation-level requirement",
  status: "Status",
  deprecated: "Deprecated",
  empty: "No endpoints match this filter.",
});
const query = ref("");
const selectedTag = ref("__all__");

const operations = computed(() => Object.entries(specification.paths).flatMap(([path, pathItem]) =>
  Object.entries(pathItem as Record<string, OpenApiOperation>)
    .filter(([method]) => methods.has(method as HttpMethod))
    .map(([method, operation]) => {
      const localization = germanApi.operations[`${method} ${path}` as keyof typeof germanApi.operations];
      const sourceTag = operation.tags?.[0] ?? "Other";
      return {
        method: method as HttpMethod,
        path,
        tag: isGerman.value ? germanApi.tags[sourceTag as keyof typeof germanApi.tags] ?? sourceTag : sourceTag,
        summary: isGerman.value ? localization?.summary ?? operation.summary ?? operation.operationId ?? path : operation.summary ?? operation.operationId ?? path,
        description: isGerman.value ? localization?.description ?? operation.description ?? "" : operation.description ?? "",
        operationId: operation.operationId ?? "",
        deprecated: Boolean(operation.deprecated),
        authenticated: Boolean(operation.security?.length),
      } satisfies Operation;
    }),
));

const tags = computed(() => Array.from(new Set(operations.value.map((operation) => operation.tag))).sort());

const filteredOperations = computed(() => {
  const needle = query.value.trim().toLowerCase();
  return operations.value.filter((operation) => {
    const matchesTag = selectedTag.value === "__all__" || operation.tag === selectedTag.value;
    const haystack = `${operation.method} ${operation.path} ${operation.summary} ${operation.description} ${operation.tag}`.toLowerCase();
    return matchesTag && (!needle || haystack.includes(needle));
  });
});

const groupedOperations = computed(() => {
  const groups = new Map<string, Operation[]>();
  for (const operation of filteredOperations.value) {
    const group = groups.get(operation.tag) ?? [];
    group.push(operation);
    groups.set(operation.tag, group);
  }
  return [...groups.entries()];
});
</script>

<template>
  <section class="api-reference" aria-labelledby="api-reference-heading">
    <div class="api-summary">
      <div>
        <p class="api-version">OpenAPI {{ specification.openapi }} · Vorrio {{ specification.info.version }}</p>
        <h2 id="api-reference-heading">{{ copy.heading }}</h2>
        <p>{{ copy.intro }}</p>
      </div>
      <a class="api-download" href="/openapi.json" download>{{ copy.download }}</a>
    </div>

    <div class="api-controls">
      <label class="api-search">
        <span class="sr-only">{{ copy.filterLabel }}</span>
        <input v-model="query" type="search" :placeholder="copy.filterPlaceholder" />
      </label>
      <label class="api-tag-filter">
        <span>{{ copy.group }}</span>
        <select v-model="selectedTag">
          <option value="__all__">{{ copy.all }}</option>
          <option v-for="tag in tags" :key="tag" :value="tag">{{ tag }}</option>
        </select>
      </label>
    </div>

    <p class="api-result-count" aria-live="polite">
      {{ filteredOperations.length }} / {{ operations.length }} {{ copy.operations }}
    </p>

    <div v-if="groupedOperations.length" class="api-groups">
      <section v-for="[tag, group] in groupedOperations" :key="tag" class="api-group">
        <div class="api-group-heading">
          <h3>{{ tag }}</h3>
          <span>{{ group.length }}</span>
        </div>

        <details v-for="operation in group" :key="`${operation.method}-${operation.path}`" class="api-operation">
          <summary>
            <span class="api-method" :data-method="operation.method">{{ operation.method.toUpperCase() }}</span>
            <code>{{ operation.path }}</code>
            <span class="api-operation-summary">{{ operation.summary }}</span>
          </summary>
          <div class="api-operation-body">
            <p v-if="operation.description">{{ operation.description }}</p>
            <p v-else>{{ copy.fallback }}</p>
            <dl>
              <div v-if="operation.operationId">
                <dt>{{ copy.operationId }}</dt>
                <dd><code>{{ operation.operationId }}</code></dd>
              </div>
              <div>
                <dt>{{ copy.authentication }}</dt>
                <dd>{{ operation.authenticated ? copy.authenticated : copy.unauthenticated }}</dd>
              </div>
              <div v-if="operation.deprecated">
                <dt>{{ copy.status }}</dt>
                <dd>{{ copy.deprecated }}</dd>
              </div>
            </dl>
          </div>
        </details>
      </section>
    </div>

    <div v-else class="api-empty">{{ copy.empty }}</div>
  </section>
</template>
