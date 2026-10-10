import { join } from "node:path";

export const MCP_URL = "https://mcp.honeybadger.io/mcp";

export const REPO = "honeybadger-io/skills";

// Where Claude Code gets the marketplace. Tests point it at a local checkout so
// an unreleased plugin can be installed end to end; users never set this.
export function marketplaceSource(env = process.env) {
  return env.HONEYBADGER_WIZARD_MARKETPLACE || REPO;
}
export const MARKETPLACE = "honeybadger";
export const PLUGIN = `honeybadger@${MARKETPLACE}`;

// Plain English instead of a slash command, so it works the same in every agent.
export const PROMPT =
  "Use the honeybadger-get-started skill to set up Honeybadger in this project.";

/**
 * Agents the wizard can set up.
 *
 *   bins    - CLI names to look for on PATH, in order
 *   mcp     - add-mcp's agent id, if add-mcp can register the MCP server
 *   launch  - args that start the agent interactively with a prompt; null if
 *             the wizard can't start it
 *
 * Every agent but Claude Code reads skills from ~/.agents/skills.
 */
export const AGENTS = [
  {
    id: "claude",
    name: "Claude Code",
    bins: ["claude"],
    launch: (prompt) => [prompt],
  },
  {
    id: "codex",
    name: "Codex",
    bins: ["codex"],
    mcp: "codex",
    launch: (prompt) => [prompt],
  },
  {
    id: "cursor",
    name: "Cursor",
    // The CLI was renamed from cursor-agent to agent.
    bins: ["agent", "cursor-agent"],
    mcp: "cursor",
    launch: (prompt) => [prompt],
  },
  {
    id: "opencode",
    name: "OpenCode",
    bins: ["opencode"],
    mcp: "opencode",
    launch: (prompt) => ["--prompt", prompt],
  },
  {
    id: "gemini",
    name: "Gemini CLI",
    bins: ["gemini"],
    mcp: "gemini-cli",
    launch: (prompt) => ["-i", prompt],
  },
  {
    id: "copilot",
    name: "GitHub Copilot CLI",
    bins: ["copilot"],
    mcp: "github-copilot-cli",
    launch: (prompt) => ["-i", prompt],
  },
  {
    id: "amp",
    name: "Amp",
    bins: ["amp"],
    launch: null,
  },
  {
    id: "pi",
    name: "Pi",
    bins: ["pi"],
    mcp: "pi",
    launch: (prompt) => [prompt],
  },
];

export function findAgent(id) {
  return AGENTS.find((agent) => agent.id === id);
}

/**
 * The steps that install Honeybadger for the chosen agents. A step is one of:
 *   { title, cmd: [bin, ...args], ignoreFailure? }  - run a command
 *   { title, copySkills: dir }                      - copy the Honeybadger skills into dir
 *   { title, mcp: [agent ids] }                     - register the MCP server with add-mcp
 *   { title, manual: [[bin, ...args], ...] }        - commands for the user to run
 *
 * Claude Code gets the plugin, which bundles the MCP server. The other agents
 * share one copy of the skills in ~/.agents/skills.
 *
 * An agent without its CLI on PATH (agent.bin unset) gets files where it can:
 * copied skills and add-mcp. Claude Code and Amp need their CLI, so they get
 * the commands to run instead.
 *
 * marketplaces is the names of Claude Code's marketplaces. If one is already
 * called honeybadger, the plugin installs from it: adding ours would fail when
 * its source differs, such as a local checkout.
 */
export function plan(agents, home, { marketplaces = [], env = process.env } = {}) {
  const byId = Object.fromEntries(agents.map((agent) => [agent.id, agent]));
  const steps = [];

  if (byId.claude && !byId.claude.bin) {
    steps.push({
      title: "Install the Honeybadger plugin in Claude Code",
      manual: [
        ["claude", "plugin", "marketplace", "add", marketplaceSource(env)],
        ["claude", "plugin", "install", PLUGIN],
      ],
    });
  } else if (byId.claude) {
    if (!marketplaces.includes(MARKETPLACE)) {
      steps.push({
        title: "Adding the Honeybadger marketplace to Claude Code",
        cmd: ["claude", "plugin", "marketplace", "add", marketplaceSource(env)],
      });
    }
    steps.push({
      title: "Installing the Honeybadger plugin in Claude Code",
      cmd: ["claude", "plugin", "install", PLUGIN],
    });
  }

  if (byId.codex?.bin) {
    // Codex also reads ~/.agents/skills, so the plugin would load the skills twice.
    steps.push({
      title: "Removing the Honeybadger plugin from Codex",
      cmd: ["codex", "plugin", "remove", PLUGIN],
      ignoreFailure: true,
    });
  }

  const shared = agents.filter((agent) => agent.id !== "claude");
  if (shared.length > 0) {
    steps.push({
      title: `Installing the Honeybadger skills for ${list(shared)}`,
      copySkills: join(home, ".agents", "skills"),
    });
  }

  const mcp = agents.filter((agent) => agent.mcp);
  if (mcp.length > 0) {
    steps.push({
      title: `Adding the MCP server to ${list(mcp)}`,
      mcp: mcp.map((agent) => agent.mcp),
    });
  }

  if (byId.amp && !byId.amp.bin) {
    steps.push({
      title: "Add the MCP server to Amp",
      manual: [["amp", "mcp", "add", "honeybadger", MCP_URL]],
    });
  } else if (byId.amp) {
    steps.push(
      {
        title: "Removing an existing honeybadger MCP server from Amp",
        cmd: ["amp", "mcp", "remove", "honeybadger"],
        ignoreFailure: true,
      },
      {
        title: "Adding the MCP server to Amp",
        cmd: ["amp", "mcp", "add", "honeybadger", MCP_URL],
      },
    );
  }

  return steps;
}

function list(agents) {
  return new Intl.ListFormat("en").format(agents.map((agent) => agent.name));
}
