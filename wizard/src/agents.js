import { join } from "node:path";

export const MCP_URLS = {
  us: "https://mcp.honeybadger.io/mcp",
  eu: "https://eu-mcp.honeybadger.io/mcp",
};

export const REPO = "honeybadger-io/skills";

// Where Claude Code gets the marketplace. Tests point it at a local checkout so
// an unreleased plugin can be installed end to end; users never set this.
export function marketplaceSource(env = process.env) {
  return env.HONEYBADGER_WIZARD_MARKETPLACE || REPO;
}
export const PLUGIN = "honeybadger@honeybadger";

// Plain English instead of a slash command, so it works the same in every agent.
export const PROMPT =
  "Use the honeybadger-get-started skill to set up Honeybadger in this project.";

/**
 * Agents the wizard can set up.
 *
 *   bins    - CLI names to look for on PATH, in order
 *   mcp     - add-mcp's agent id, if add-mcp can register the MCP server
 *   launch  - args that start the agent interactively with a prompt; null if
 *             it can't take one
 *   note    - shown after installing
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
    note: "Pi needs an extension to use MCP servers: pi install npm:pi-mcp-adapter",
  },
];

export function findAgent(id) {
  return AGENTS.find((agent) => agent.id === id);
}

/**
 * The steps that install Honeybadger for the chosen agents. A step is one of:
 *   { title, cmd: [bin, ...args], ignoreFailure? }  - run a command
 *   { title, copySkills: dir }                      - copy the honeybadger-* skills into dir
 *   { title, removeSkills: dir }                    - remove copied honeybadger-* skills
 *   { title, mcp: [agent ids], url }                - register the MCP server with add-mcp
 *
 * On US, Claude Code gets the plugin, which updates itself and bundles the US
 * MCP server. The plugin can't point at the EU server, so on EU Claude Code
 * gets copied skills and the EU server instead. The other agents share one
 * copy of the skills in ~/.agents/skills.
 */
export function plan(agents, region, home) {
  const ids = new Set(agents.map((agent) => agent.id));
  const url = MCP_URLS[region];
  const steps = [];

  if (ids.has("claude")) {
    const claudeSkills = join(process.env.CLAUDE_CONFIG_DIR ?? join(home, ".claude"), "skills");
    const removeServer = {
      title: "Removing an existing honeybadger MCP server from Claude Code",
      cmd: ["claude", "mcp", "remove", "--scope", "user", "honeybadger"],
      ignoreFailure: true,
    };
    if (region === "us") {
      steps.push(
        {
          title: "Adding the Honeybadger marketplace to Claude Code",
          cmd: ["claude", "plugin", "marketplace", "add", marketplaceSource()],
        },
        {
          title: "Installing the Honeybadger plugin in Claude Code",
          cmd: ["claude", "plugin", "install", PLUGIN],
        },
        // Left over from an EU install; the plugin replaces both.
        { title: "Removing copied skills from Claude Code", removeSkills: claudeSkills },
        removeServer,
      );
    } else {
      steps.push(
        {
          title: "Removing the US Honeybadger plugin from Claude Code",
          cmd: ["claude", "plugin", "uninstall", PLUGIN],
          ignoreFailure: true,
        },
        { title: "Installing the Honeybadger skills for Claude Code", copySkills: claudeSkills },
        removeServer,
        {
          title: "Adding the EU MCP server to Claude Code",
          cmd: ["claude", "mcp", "add", "--scope", "user", "--transport", "http", "honeybadger", url],
        },
      );
    }
  }

  if (ids.has("codex")) {
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
      title: `Adding the ${region === "eu" ? "EU " : ""}MCP server to ${list(mcp)}`,
      mcp: mcp.map((agent) => agent.mcp),
      url,
    });
  }

  if (ids.has("amp")) {
    steps.push(
      {
        title: "Removing an existing honeybadger MCP server from Amp",
        cmd: ["amp", "mcp", "remove", "honeybadger"],
        ignoreFailure: true,
      },
      {
        title: `Adding the ${region === "eu" ? "EU " : ""}MCP server to Amp`,
        cmd: ["amp", "mcp", "add", "honeybadger", url],
      },
    );
  }

  return steps;
}

function list(agents) {
  return new Intl.ListFormat("en").format(agents.map((agent) => agent.name));
}
