// Copies the repo's skills and license into the package before `npm pack` /
// `npm publish`, so the published wizard installs the skills from the same commit.
// With --clean (after packing), removes them again, so a checkout keeps
// installing the repo's own skills.
import { copyFileSync, cpSync, rmSync } from "node:fs";
import { fileURLToPath } from "node:url";

const path = (rel) => fileURLToPath(new URL(rel, import.meta.url));
const skills = path("../skills");
const license = path("../LICENSE");

rmSync(skills, { recursive: true, force: true });
rmSync(license, { force: true });
if (!process.argv.includes("--clean")) {
  cpSync(path("../../skills"), skills, { recursive: true });
  copyFileSync(path("../../LICENSE"), license);
}
