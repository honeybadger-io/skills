import {
  accessSync,
  constants,
  cpSync,
  existsSync,
  mkdirSync,
  readdirSync,
  rmSync,
} from "node:fs";
import { delimiter, join } from "node:path";
import { fileURLToPath } from "node:url";
import { upsertServer } from "add-mcp";

/** The skills to install: bundled in the package, or the repo's own when run from a checkout. */
export function skillsSource() {
  for (const rel of ["../skills", "../../skills"]) {
    const dir = fileURLToPath(new URL(rel, import.meta.url));
    if (existsSync(dir)) return dir;
  }
  throw new Error("Can't find the Honeybadger skills to install.");
}

/**
 * Replaces each honeybadger-* skill from src in dest. Other skills in dest,
 * including other honeybadger-* ones, are left alone. Returns the names copied.
 */
export function copySkills(src, dest) {
  const names = readdirSync(src, { withFileTypes: true })
    .filter((entry) => entry.isDirectory() && entry.name.startsWith("honeybadger-"))
    .map((entry) => entry.name);
  mkdirSync(dest, { recursive: true });
  for (const name of names) {
    rmSync(join(dest, name), { recursive: true, force: true });
    cpSync(join(src, name), join(dest, name), { recursive: true });
  }
  return names;
}

/** Registers the honeybadger MCP server with each add-mcp agent, replacing an existing one. */
export function addMcpServer(agents, url) {
  for (const agent of agents) {
    const result = upsertServer(agent, "honeybadger", { type: "http", url });
    if (!result.success) {
      throw new Error(`Couldn't update ${result.path}: ${result.error}`);
    }
  }
}

/** Returns the first of bins found on PATH, or undefined. */
export function findBin(bins, path = process.env.PATH ?? "") {
  const exts =
    process.platform === "win32"
      ? (process.env.PATHEXT ?? ".EXE;.CMD;.BAT").split(";")
      : [""];
  for (const bin of bins) {
    for (const dir of path.split(delimiter).filter(Boolean)) {
      for (const ext of exts) {
        try {
          accessSync(join(dir, bin + ext), constants.X_OK);
          return bin;
        } catch {
          // keep looking
        }
      }
    }
  }
  return undefined;
}

/** True if dir looks like an app: a git repo or a common dependency manifest. */
export function looksLikeProject(dir) {
  const markers = [
    ".git", "package.json", "Gemfile", "requirements.txt", "pyproject.toml",
    "composer.json", "mix.exs", "go.mod", "Cargo.toml", "pom.xml", "build.gradle",
  ];
  return markers.some((marker) => existsSync(join(dir, marker)));
}
