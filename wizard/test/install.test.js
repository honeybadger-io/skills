import assert from "node:assert/strict";
import { execFileSync } from "node:child_process";
import { chmodSync, mkdirSync, mkdtempSync, readFileSync, writeFileSync } from "node:fs";
import { tmpdir } from "node:os";
import { join } from "node:path";
import { test } from "node:test";
import { getAgentTypes } from "add-mcp";
import { AGENTS, MCP_URLS, PLUGIN, REPO, SKILLS_CLI, findAgent, plan, repoSource } from "../src/agents.js";
import { banner, colorSupport } from "../src/banner.js";
import { commandEnv, findBin, isCI, looksLikeProject } from "../src/install.js";

const tmp = () => mkdtempSync(join(tmpdir(), "hb-wizard-"));

// add-mcp reads the home directory when it loads, so this runs in a child
// process with HOME pointed at a temp dir, away from your real configs.
test("addMcpServer keeps other servers and replaces ours", () => {
  const home = tmp();
  const file = join(home, ".cursor", "mcp.json");
  mkdirSync(join(home, ".cursor"));
  writeFileSync(file, JSON.stringify({ mcpServers: { other: { url: "https://example.com/mcp" } } }));
  const install = new URL("../src/install.js", import.meta.url).href;
  const script = `
    const { addMcpServer } = await import(${JSON.stringify(install)});
    addMcpServer(["cursor"], "https://old.example.com/mcp");
    addMcpServer(["cursor"], ${JSON.stringify(MCP_URLS.us)});
  `;
  execFileSync(process.execPath, ["--input-type=module", "-e", script], {
    env: { ...process.env, HOME: home, USERPROFILE: home },
  });
  assert.deepEqual(JSON.parse(readFileSync(file, "utf8")).mcpServers, {
    other: { url: "https://example.com/mcp" },
    honeybadger: { url: MCP_URLS.us },
  });
});

test("findBin returns the first bin on PATH", { skip: process.platform === "win32" }, () => {
  const dir = tmp();
  writeFileSync(join(dir, "cursor-agent"), "");
  chmodSync(join(dir, "cursor-agent"), 0o755);
  assert.equal(findBin(["agent", "cursor-agent"], dir), "cursor-agent");
  assert.equal(findBin(["claude"], dir), undefined);
});

test("looksLikeProject", () => {
  const dir = tmp();
  assert.equal(looksLikeProject(dir), false);
  writeFileSync(join(dir, "Gemfile"), "");
  assert.equal(looksLikeProject(dir), true);
});

const everyone = () => AGENTS.map((agent) => ({ ...agent, bin: agent.bins[0] }));

test("Claude Code gets the plugin and nothing else", () => {
  const steps = plan([{ ...findAgent("claude"), bin: "claude" }], "us", { env: {} });
  assert.deepEqual(
    steps.map((s) => s.cmd?.join(" ")),
    [
      "claude plugin marketplace add honeybadger-io/skills",
      `claude plugin install ${PLUGIN} --config mcp_url=${MCP_URLS.us}`,
    ],
  );
});

test("Claude Code keeps an existing honeybadger marketplace instead of adding ours", () => {
  const claude = [{ ...findAgent("claude"), bin: "claude" }];
  const adds = (marketplaces) =>
    plan(claude, "us", { marketplaces, env: {} }).filter((s) => s.cmd?.includes("marketplace"));
  assert.equal(adds([]).length, 1);
  assert.equal(adds(["honeybadger"]).length, 0);
});

test("EU points every agent at the EU server and never the US one", () => {
  const steps = plan(everyone(), "eu", { env: {} });
  const text = JSON.stringify(steps);
  assert.ok(!text.includes(MCP_URLS.us));
  assert.ok(steps.some((s) => s.cmd?.join(" ") === `claude plugin install ${PLUGIN} --config mcp_url=${MCP_URLS.eu}`));
  assert.equal(steps.find((s) => s.mcp).url, MCP_URLS.eu);
  assert.ok(steps.some((s) => s.cmd?.join(" ") === `amp mcp add honeybadger ${MCP_URLS.eu}`));
});

test("the plugin's mcp_url option allows exactly the wizard's two URLs, US by default", () => {
  const manifest = JSON.parse(readFileSync(new URL("../../.claude-plugin/plugin.json", import.meta.url), "utf8"));
  const option = manifest.userConfig.mcp_url;
  assert.equal(option.default, MCP_URLS.us);
  assert.deepEqual(option.options, [MCP_URLS.us, MCP_URLS.eu]);
  assert.equal(manifest.mcpServers.honeybadger.url, "${user_config.mcp_url}");
});

test("the marketplace and skills come from the GitHub repo, or a checkout in tests", () => {
  assert.equal(repoSource({}), REPO);
  assert.equal(repoSource({ HONEYBADGER_WIZARD_MARKETPLACE: "/src/skills" }), "/src/skills");
});

const skillsInstall = (steps) => steps.filter((s) => s.cmd?.includes(SKILLS_CLI));

test("other agents get the skills in one skills CLI run, and one MCP step", () => {
  const steps = plan(everyone(), "us", { env: {} });
  const installs = skillsInstall(steps);
  assert.equal(installs.length, 1);
  assert.deepEqual(installs[0].cmd, [
    "npx", "-y", SKILLS_CLI, "add", REPO, "--global",
    "--agent", "codex", "cursor", "opencode", "gemini-cli", "github-copilot", "amp", "pi", "universal",
    "--skill", "*", "--yes",
  ]);
  assert.equal(installs[0].env.DISABLE_TELEMETRY, "1");
  const mcp = steps.filter((s) => s.mcp);
  assert.equal(mcp.length, 1);
  assert.deepEqual(mcp[0].mcp, AGENTS.filter((a) => a.mcp).map((a) => a.mcp));
  assert.ok(steps.some((s) => s.cmd?.join(" ") === `amp mcp add honeybadger ${MCP_URLS.us}`));
});

test("add-mcp knows every agent id we pass it", () => {
  const known = getAgentTypes();
  for (const agent of AGENTS.filter((a) => a.mcp)) {
    assert.ok(known.includes(agent.mcp), `add-mcp doesn't know ${agent.mcp}`);
  }
});

test("agents picked without their CLI run nothing but the skills CLI", () => {
  const agents = AGENTS.map((agent) => ({ ...agent, bin: undefined }));
  const steps = plan(agents, "us", { env: {} });
  assert.deepEqual(steps.filter((s) => s.cmd), skillsInstall(steps));
  assert.deepEqual(steps.filter((s) => s.manual).map((s) => s.manual), [
    [
      ["claude", "plugin", "marketplace", "add", REPO],
      ["claude", "plugin", "install", PLUGIN, "--config", `mcp_url=${MCP_URLS.us}`],
    ],
    [["amp", "mcp", "add", "honeybadger", MCP_URLS.us]],
  ]);
});

test("banner fits the terminal: bolt and wordmark, wordmark alone, or nothing", () => {
  const details = [["release", "honeybadger wizard v0.0.0"], ["agents", "x".repeat(200)]];
  const widest = (text) => Math.max(...text.split("\n").map((line) => line.length));
  const wide = banner({ columns: 120, details });
  assert.ok(wide.includes("$$$") && widest(wide) <= 120);
  const narrow = banner({ columns: 80, details });
  assert.ok(!narrow.includes("$$$") && narrow.includes("/____/") && widest(narrow) <= 80);
  assert.equal(banner({ columns: 40, details }), "");
});

test("banner color follows Node's color support check", () => {
  assert.equal(colorSupport({ NO_COLOR: "1", COLORTERM: "truecolor" }), null);
  assert.equal(colorSupport({ FORCE_COLOR: "0", COLORTERM: "truecolor" }), null);
  assert.equal(colorSupport({ TERM: "dumb" }), null);
  assert.equal(colorSupport({ COLORTERM: "truecolor" }), "truecolor");
  assert.equal(colorSupport({ TERM: "xterm-256color" }), "ansi256");
  assert.ok(!banner({ columns: 120, details: [["a", "b"]] }).includes("\x1b["));
  assert.ok(banner({ columns: 120, color: "truecolor", details: [["a", "b"]] }).includes("\x1b[38;2;234;89;55m"));
});

test("Other agent gets the skills and the region's MCP config to add", () => {
  const other = [{ ...findAgent("other"), bin: undefined }];
  for (const region of ["us", "eu"]) {
    const steps = plan(other, region, { env: {} });
    assert.ok(!steps.some((s) => s.mcp));
    assert.deepEqual(steps.filter((s) => s.cmd), skillsInstall(steps));
    assert.ok(skillsInstall(steps)[0].cmd.includes("universal"));
    const snippet = JSON.parse(steps.find((s) => s.snippet).snippet);
    assert.deepEqual(snippet, { mcpServers: { honeybadger: { type: "http", url: MCP_URLS[region] } } });
  }
});

test("Other agent is never found on PATH, so --yes doesn't pick it", () => {
  assert.equal(findBin(findAgent("other").bins), undefined);
});

test("isCI", () => {
  assert.equal(isCI({ CI: "true" }), true);
  assert.equal(isCI({ CI: "1" }), true);
  assert.equal(isCI({ CI: "false" }), false);
  assert.equal(isCI({}), false);
});

test("every agent but Claude Code has a skills CLI name", () => {
  for (const agent of AGENTS) assert.equal(Boolean(agent.skills), agent.id !== "claude", agent.id);
});

test("commandEnv drops the npx settings the wizard was started with, only for npx", () => {
  const base = { PATH: "/bin", npm_config_package: "@honeybadger-io/wizard", npm_config_call: "wizard" };
  assert.deepEqual(commandEnv("npx", { DISABLE_TELEMETRY: "1" }, base), { PATH: "/bin", DISABLE_TELEMETRY: "1" });
  assert.deepEqual(commandEnv("claude", {}, base), base);
});
