// Copies the repo's skills and license into the package before `npm pack` /
// `npm publish`, so the published wizard installs the skills from the same commit.
import { copyFileSync, cpSync, rmSync } from "node:fs";
import { fileURLToPath } from "node:url";

const from = fileURLToPath(new URL("../../skills", import.meta.url));
const to = fileURLToPath(new URL("../skills", import.meta.url));

rmSync(to, { recursive: true, force: true });
cpSync(from, to, { recursive: true });
copyFileSync(
  fileURLToPath(new URL("../../LICENSE", import.meta.url)),
  fileURLToPath(new URL("../LICENSE", import.meta.url)),
);
