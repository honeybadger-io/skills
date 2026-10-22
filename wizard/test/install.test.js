import assert from "node:assert/strict";
import { execFileSync } from "node:child_process";
import { chmodSync, mkdirSync, mkdtempSync, readFileSync, writeFileSync, readdirSync, existsSync } from "node:fs";
import { tmpdir } from "node:os";
import { join } from "node:path";
import { test } from "node:test";
import { getAgentTypes } from "add-mcp";
import { AGENTS, MCP_URLS, PLUGIN, REPO, findAgent, marketplaceSource, plan } from "../src/agents.js";
import { banner, colorSupport } from "../src/banner.js";
import {
  copySkills,
  existingSkills,
  findBin,
  isCI,
  looksLikeProject,
  skillsSource,
} from "../src/install.js";

const tmp = () => mkdtempSync(join(tmpdir(), "hb-wizard-"));

test("copySkills copies only honeybadger-* skills and replaces stale files", () => {
  const src = tmp();
  mkdirSync(join(src, "honeybadger-a"));
  writeFileSync(join(src, "honeybadger-a", "SKILL.md"), "new");
  mkdirSync(join(src, "other-skill"));
  const dest = tmp();
  mkdirSync(join(dest, "honeybadger-a"));
  writeFileSync(join(dest, "honeybadger-a", "stale.md"), "old");
  mkdirSync(join(dest, "someone-elses"));

  assert.deepEqual(copySkills(src, dest), ["honeybadger-a"]);
  assert.deepEqual(readdirSync(join(dest, "honeybadger-a")), ["SKILL.md"]);
  assert.ok(existsSync(join(dest, "someone-elses")));
  assert.ok(!existsSync(join(dest, "other-skill")));
});

test("existingSkills lists only our skills already in dest", () => {
  const src = tmp();
  mkdirSync(join(src, "honeybadger-a"));
  mkdirSync(join(src, "honeybadger-b"));
  const dest = tmp();
  mkdirSync(join(dest, "honeybadger-a"));
  mkdirSync(join(dest, "honeybadger-mine"));
  assert.deepEqual(existingSkills(src, dest), ["honeybadger-a"]);
  assert.deepEqual(existingSkills(src, join(dest, "missing")), []);
});

test("copySkills leaves other honeybadger-* skills alone", () => {
  const src = tmp();
  mkdirSync(join(src, "honeybadger-a"));
  const dest = tmp();
  mkdirSync(join(dest, "honeybadger-mine"));
  copySkills(src, dest);
  assert.deepEqual(readdirSync(dest).sort(), ["honeybadger-a", "honeybadger-mine"]);
});

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

test("skillsSource finds the get-started skill", () => {
  assert.ok(existsSync(join(skillsSource(), "honeybadger-get-started", "SKILL.md")));
});

const everyone = () => AGENTS.map((agent) => ({ ...agent, bin: agent.bins[0] }));

test("Claude Code gets the plugin and nothing else", () => {
  const steps = plan([{ ...findAgent("claude"), bin: "claude" }], "us", "/home/me", { env: {} });
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
    plan(claude, "us", "/home/me", { marketplaces, env: {} }).filter((s) => s.cmd?.includes("marketplace"));
  assert.equal(adds([]).length, 1);
  assert.equal(adds(["honeybadger"]).length, 0);
});

test("EU points every agent at the EU server and never the US one", () => {
  const steps = plan(everyone(), "eu", "/home/me", { env: {} });
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

test("the marketplace defaults to the GitHub repo and can point at a checkout", () => {
  assert.equal(marketplaceSource({}), REPO);
  assert.equal(marketplaceSource({ HONEYBADGER_WIZARD_MARKETPLACE: "/src/skills" }), "/src/skills");
});

test("other agents share one copy of the skills and one MCP step", () => {
  const steps = plan(everyone(), "us", "/home/me", { env: {} });
  const copies = steps.filter((s) => s.copySkills === join("/home/me", ".agents", "skills"));
  assert.equal(copies.length, 1);
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

test("agents picked without their CLI get files or commands to run, never run anything", () => {
  const agents = AGENTS.map((agent) => ({ ...agent, bin: undefined }));
  const steps = plan(agents, "us", "/home/me", { env: {} });
  assert.ok(!steps.some((s) => s.cmd));
  assert.ok(!steps.some((s) => s.copySkills?.includes(".claude")));
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

test("Other agent gets the shared skills and the region's MCP config to add, nothing run", () => {
  const other = [{ ...findAgent("other"), bin: undefined }];
  for (const region of ["us", "eu"]) {
    const steps = plan(other, region, "/home/me", { env: {} });
    assert.ok(!steps.some((s) => s.cmd || s.mcp));
    assert.ok(steps.some((s) => s.copySkills === join("/home/me", ".agents", "skills")));
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
