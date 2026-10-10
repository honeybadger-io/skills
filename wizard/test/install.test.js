import assert from "node:assert/strict";
import { execFileSync } from "node:child_process";
import { chmodSync, mkdirSync, mkdtempSync, readFileSync, writeFileSync, readdirSync, existsSync } from "node:fs";
import { tmpdir } from "node:os";
import { join } from "node:path";
import { test } from "node:test";
import { getAgentTypes } from "add-mcp";
import { AGENTS, MCP_URLS, PLUGIN, REPO, findAgent, marketplaceSource, plan } from "../src/agents.js";
import {
  copySkills,
  findBin,
  looksLikeProject,
  removeSkills,
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

test("removeSkills removes only honeybadger-* skills", () => {
  const dir = tmp();
  mkdirSync(join(dir, "honeybadger-a"));
  mkdirSync(join(dir, "someone-elses"));
  assert.deepEqual(removeSkills(dir), ["honeybadger-a"]);
  assert.deepEqual(readdirSync(dir), ["someone-elses"]);
  assert.deepEqual(removeSkills(join(dir, "missing")), []);
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
    addMcpServer(["cursor"], ${JSON.stringify(MCP_URLS.us)});
    addMcpServer(["cursor"], ${JSON.stringify(MCP_URLS.eu)});
  `;
  execFileSync(process.execPath, ["--input-type=module", "-e", script], {
    env: { ...process.env, HOME: home, USERPROFILE: home },
  });
  assert.deepEqual(JSON.parse(readFileSync(file, "utf8")).mcpServers, {
    other: { url: "https://example.com/mcp" },
    honeybadger: { url: MCP_URLS.eu },
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

test("EU never uses the plugin or the US server", () => {
  const steps = plan(everyone(), "eu", "/home/me");
  const text = JSON.stringify(steps);
  assert.ok(!text.includes(MCP_URLS.us));
  assert.ok(text.includes(MCP_URLS.eu));
  const pluginSteps = steps.filter((s) => s.cmd?.includes(PLUGIN));
  assert.ok(pluginSteps.length > 0 && pluginSteps.every((s) => s.ignoreFailure), "EU only removes plugins");
});

test("US installs the Claude Code plugin and cleans up an EU install", () => {
  const steps = plan([findAgent("claude")], "us", "/home/me");
  assert.ok(steps.some((s) => s.cmd?.join(" ") === `claude plugin install ${PLUGIN}`));
  assert.ok(steps.some((s) => s.removeSkills === join("/home/me", ".claude", "skills")));
  assert.ok(!steps.some((s) => s.copySkills || s.mcp));
});

test("the marketplace defaults to the GitHub repo and can point at a checkout", () => {
  assert.equal(marketplaceSource({}), REPO);
  assert.equal(marketplaceSource({ HONEYBADGER_WIZARD_MARKETPLACE: "/src/skills" }), "/src/skills");
});

test("other agents share one copy of the skills and one MCP step", () => {
  const steps = plan(everyone(), "us", "/home/me");
  const copies = steps.filter((s) => s.copySkills === join("/home/me", ".agents", "skills"));
  assert.equal(copies.length, 1);
  const mcp = steps.filter((s) => s.mcp);
  assert.equal(mcp.length, 1);
  assert.deepEqual(mcp[0].mcp, AGENTS.filter((a) => a.mcp).map((a) => a.mcp));
  assert.equal(mcp[0].url, MCP_URLS.us);
  assert.ok(steps.some((s) => s.cmd?.join(" ") === `amp mcp add honeybadger ${MCP_URLS.us}`));
});

test("add-mcp knows every agent id we pass it", () => {
  const known = getAgentTypes();
  for (const agent of AGENTS.filter((a) => a.mcp)) {
    assert.ok(known.includes(agent.mcp), `add-mcp doesn't know ${agent.mcp}`);
  }
});
