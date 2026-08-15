<script setup lang="ts">
import { computed, ref } from "vue";
import specification from "../../../api/openapi.json";

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
const query = ref("");
const selectedTag = ref("All");

const operations = Object.entries(specification.paths).flatMap(([path, pathItem]) =>
  Object.entries(pathItem as Record<string, OpenApiOperation>)
    .filter(([method]) => methods.has(method as HttpMethod))
    .map(([method, operation]) => ({
      method: method as HttpMethod,
      path,
      tag: operation.tags?.[0] ?? "Other",
      summary: operation.summary ?? operation.operationId ?? path,
      description: operation.description ?? "",
      operationId: operation.operationId ?? "",
      deprecated: Boolean(operation.deprecated),
      authenticated: Boolean(operation.security?.length),
    } satisfies Operation)),
);

const tags = ["All", ...Array.from(new Set(operations.map((operation) => operation.tag))).sort()];

const filteredOperations = computed(() => {
  const needle = query.value.trim().toLowerCase();
  return operations.filter((operation) => {
    const matchesTag = selectedTag.value === "All" || operation.tag === selectedTag.value;
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
        <h2 id="api-reference-heading">Explore the REST API</h2>
        <p>
          Browse the checked-in public contract without connecting to a household. Requests are not
          executed from this documentation site.
        </p>
      </div>
      <a class="api-download" href="/openapi.json" download>Download OpenAPI JSON</a>
    </div>

    <div class="api-controls">
      <label class="api-search">
        <span class="sr-only">Filter endpoints</span>
        <input v-model="query" type="search" placeholder="Filter by path, method or summary" />
      </label>
      <label class="api-tag-filter">
        <span>Group</span>
        <select v-model="selectedTag">
          <option v-for="tag in tags" :key="tag" :value="tag">{{ tag }}</option>
        </select>
      </label>
    </div>

    <p class="api-result-count" aria-live="polite">
      {{ filteredOperations.length }} of {{ operations.length }} operations
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
            <p v-else>This operation is defined in the canonical Vorrio OpenAPI contract.</p>
            <dl>
              <div v-if="operation.operationId">
                <dt>Operation ID</dt>
                <dd><code>{{ operation.operationId }}</code></dd>
              </div>
              <div>
                <dt>Authentication</dt>
                <dd>{{ operation.authenticated ? "Session or supported scoped bearer token" : "No operation-level requirement" }}</dd>
              </div>
              <div v-if="operation.deprecated">
                <dt>Status</dt>
                <dd>Deprecated</dd>
              </div>
            </dl>
          </div>
        </details>
      </section>
    </div>

    <div v-else class="api-empty">No endpoints match this filter.</div>
  </section>
</template>
