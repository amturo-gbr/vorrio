import { copyFile, mkdir } from "node:fs/promises";
import { fileURLToPath } from "node:url";
import path from "node:path";

const docsDir = path.resolve(path.dirname(fileURLToPath(import.meta.url)), "..");
const repositoryDir = path.resolve(docsDir, "..");
const publicDir = path.join(docsDir, "public");

await mkdir(path.join(publicDir, "brand"), { recursive: true });

await Promise.all([
  copyFile(path.join(docsDir, "api", "openapi.json"), path.join(publicDir, "openapi.json")),
  copyFile(
    path.join(repositoryDir, "website", "assets", "brand", "vorrio-mark.png"),
    path.join(publicDir, "brand", "vorrio-mark.png"),
  ),
  copyFile(
    path.join(repositoryDir, "website", "assets", "vorrio-icon.png"),
    path.join(publicDir, "vorrio-icon.png"),
  ),
  copyFile(
    path.join(repositoryDir, "website", "assets", "vorrio-social-card-en.png"),
    path.join(publicDir, "vorrio-social-card-en.png"),
  ),
]);

console.log("Prepared docs assets from the canonical website and OpenAPI sources.");
