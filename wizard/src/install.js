import { accessSync, constants, existsSync } from "node:fs";
import { delimiter, join } from "node:path";
import { upsertServer } from "add-mcp";

/** Registers the honeybadger MCP server with each add-mcp agent, replacing an existing one. */
export function addMcpServer(agents, url) {
  for (const agent of agents) {
    const result = upsertServer(agent, "honeybadger", { type: "http", url });
    if (!result.success) {
      throw new Error(`Couldn't update ${result.path}: ${result.error}`);
    }
  }
}

/**
 * The environment to run bin with. Started through npx, the wizard inherits npx's settings for its own package
 * (npm_config_package, npm_config_call); an npx it runs would read them and run the wizard's package instead.
 */
export function commandEnv(bin, extra = {}, base = process.env) {
  const env = { ...base, ...extra };
  if (bin === "npx") {
    // npm reads npm_config_* in any case
    for (const key of Object.keys(env)) {
      if (["npm_config_package", "npm_config_call"].includes(key.toLowerCase())) delete env[key];
    }
  }
  return env;
}

/** True if version (like process.versions.node) is at least min, comparing major.minor.patch. */
export function nodeAtLeast(min, version = process.versions.node) {
  const parse = (v) => v.split(".").map((part) => Number.parseInt(part, 10) || 0);
  const [a, b] = [parse(version), parse(min)];
  for (let i = 0; i < 3; i++) {
    if ((a[i] ?? 0) !== (b[i] ?? 0)) return (a[i] ?? 0) > (b[i] ?? 0);
  }
  return true;
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

/** True when running in CI. Some CI systems give jobs a terminal, so a TTY check alone isn't enough. */
export function isCI(env = process.env) {
  return Boolean(env.CI) && env.CI !== "false" && env.CI !== "0";
}

/** True if dir looks like an app: a git repo or a common dependency manifest. */
export function looksLikeProject(dir) {
  const markers = [
    ".git", "package.json", "Gemfile", "requirements.txt", "pyproject.toml",
    "composer.json", "mix.exs", "go.mod", "Cargo.toml", "pom.xml", "build.gradle",
  ];
  return markers.some((marker) => existsSync(join(dir, marker)));
}
