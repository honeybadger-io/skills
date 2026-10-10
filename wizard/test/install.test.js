import assert from "node:assert/strict";
import { chmodSync, mkdirSync, mkdtempSync, readFileSync, writeFileSync, readdirSync, existsSync } from "node:fs";
import { tmpdir } from "node:os";
import { join } from "node:path";
import { test } from "node:test";
import { AGENTS, MCP_URLS, PLUGIN } from "../src/agents.js";
import { addMcpServer, copySkills, findBin, looksLikeProject, skillsSource } from "../src/install.js";

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

test("addMcpServer keeps other servers and replaces ours", () => {
  const file = join(tmp(), ".cursor", "mcp.json");
  addMcpServer(file, MCP_URLS.us);
  const config = JSON.parse(readFileSync(file, "utf8"));
  config.mcpServers.other = { url: "https://example.com/mcp" };
  writeFileSync(file, JSON.stringify(config));

  addMcpServer(file, MCP_URLS.eu);
  assert.deepEqual(JSON.parse(readFileSync(file, "utf8")).mcpServers, {
    other: { url: "https://example.com/mcp" },
    honeybadger: { url: MCP_URLS.eu },
  });
});

test("addMcpServer refuses to overwrite invalid JSON", () => {
  const file = join(tmp(), "mcp.json");
  writeFileSync(file, "{ nope");
  assert.throws(() => addMcpServer(file, MCP_URLS.us), /isn't valid JSON/);
  assert.equal(readFileSync(file, "utf8"), "{ nope");
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

test("US installs the plugin; EU removes it and uses the EU server", () => {
  for (const agent of AGENTS) {
    const us = agent.steps("us", "/home/me");
    const eu = agent.steps("eu", "/home/me");
    const usText = JSON.stringify(us);
    const euText = JSON.stringify(eu);

    assert.ok(!euText.includes(MCP_URLS.us), `${agent.id} EU mentions the US server`);
    assert.ok(euText.includes(MCP_URLS.eu), `${agent.id} EU doesn't add the EU server`);
    if (agent.id === "cursor") {
      assert.ok(usText.includes(MCP_URLS.us));
    } else {
      assert.ok(us.some((s) => s.cmd?.includes(PLUGIN)), `${agent.id} US doesn't install the plugin`);
      const removal = eu.find((s) => s.cmd?.includes(PLUGIN));
      assert.ok(removal?.ignoreFailure, `${agent.id} EU doesn't remove the plugin`);
    }
  }
});
