export const MCP_URLS = {
  us: "https://mcp.honeybadger.io/mcp",
  eu: "https://eu-mcp.honeybadger.io/mcp",
};

export const REPO = "honeybadger-io/skills";

// Where Claude Code's marketplace and the skills CLI get this repo. Tests point it at a local checkout so
// unreleased skills and plugin changes can be installed end to end; users never set this.
export function repoSource(env = process.env) {
  return env.HONEYBADGER_WIZARD_MARKETPLACE || REPO;
}

// The skills CLI (skills.sh) installs the skills for every agent but Claude Code. Pinned: it runs through npx.
export const SKILLS_CLI = "skills@1.7.6";
export const MARKETPLACE = "honeybadger";
export const PLUGIN = `honeybadger@${MARKETPLACE}`;

// Plain English instead of a slash command, so it works the same in every agent.
export const PROMPT =
  "Use the honeybadger-get-started skill to set up Honeybadger in this project.";

/**
 * Agents the wizard can set up.
 *
 *   bins     - CLI names to look for on PATH, in order
 *   skills   - the skills CLI's name for the agent
 *   mcp      - add-mcp's agent id, if add-mcp can register the MCP server
 *   launch   - args that start the agent interactively with a prompt; null if
 *              the wizard can't start it
 *   hint     - shown next to the agent in the picker
 *   listName - the name used mid-sentence, if different
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
    skills: "codex",
    name: "Codex",
    bins: ["codex"],
    mcp: "codex",
    launch: (prompt) => [prompt],
  },
  {
    id: "cursor",
    skills: "cursor",
    name: "Cursor",
    // The CLI was renamed from cursor-agent to agent.
    bins: ["agent", "cursor-agent"],
    mcp: "cursor",
    launch: (prompt) => [prompt],
  },
  {
    id: "opencode",
    skills: "opencode",
    name: "OpenCode",
    bins: ["opencode"],
    mcp: "opencode",
    launch: (prompt) => ["--prompt", prompt],
  },
  {
    id: "gemini",
    skills: "gemini-cli",
    name: "Gemini CLI",
    bins: ["gemini"],
    mcp: "gemini-cli",
    launch: (prompt) => ["-i", prompt],
  },
  {
    id: "copilot",
    skills: "github-copilot",
    name: "GitHub Copilot CLI",
    bins: ["copilot"],
    mcp: "github-copilot-cli",
    launch: (prompt) => ["-i", prompt],
  },
  {
    id: "amp",
    skills: "amp",
    name: "Amp",
    bins: ["amp"],
    launch: null,
  },
  {
    id: "pi",
    skills: "pi",
    name: "Pi",
    bins: ["pi"],
    mcp: "pi",
    launch: (prompt) => [prompt],
  },
  {
    // Any agent that reads ~/.agents/skills. The wizard can't know where its MCP config lives, so it prints the
    // config to add.
    id: "other",
    skills: "universal",
    name: "Other agent",
    listName: "your other agent",
    bins: [],
    launch: null,
    hint: "copies the skills to ~/.agents/skills and shows the MCP config to add",
  },
];

export function findAgent(id) {
  return AGENTS.find((agent) => agent.id === id);
}

/**
 * The steps that install Honeybadger for the chosen agents. A step is one of:
 *   { title, cmd: [bin, ...args], env?, ignoreFailure? } - run a command
 *   { title, mcp: [agent ids], url }                - register the MCP server with add-mcp
 *   { title, manual: [[bin, ...args], ...] }        - commands for the user to run
 *   { title, snippet, url }                         - MCP server details for the user to add
 *
 * Claude Code gets the plugin, which bundles the MCP server. The plugin's
 * mcp_url option picks the region's server, so the wizard never writes Claude
 * Code's MCP config. The skills CLI installs the skills for the other agents
 * from GitHub; they all read its one global copy in ~/.agents/skills.
 *
 * An agent without its CLI on PATH (agent.bin unset) still gets the skills and,
 * where add-mcp can write it, the MCP config. Claude Code and Amp need their
 * CLI, so they get the commands to run instead.
 *
 * marketplaces is the names of Claude Code's marketplaces. If one is already
 * called honeybadger, the plugin installs from it: adding ours would fail when
 * its source differs, such as a local checkout.
 */
export function plan(agents, region, { marketplaces = [], env = process.env } = {}) {
  const byId = Object.fromEntries(agents.map((agent) => [agent.id, agent]));
  const url = MCP_URLS[region];
  const server = region === "eu" ? "the EU MCP server" : "the MCP server";
  const install = ["claude", "plugin", "install", PLUGIN, "--config", `mcp_url=${url}`];
  const steps = [];

  if (byId.claude && !byId.claude.bin) {
    steps.push({
      title: "Install the Honeybadger plugin in Claude Code",
      manual: [
        ["claude", "plugin", "marketplace", "add", repoSource(env)],
        install,
      ],
    });
  } else if (byId.claude) {
    if (!marketplaces.includes(MARKETPLACE)) {
      steps.push({
        title: "Adding the Honeybadger marketplace to Claude Code",
        cmd: ["claude", "plugin", "marketplace", "add", repoSource(env)],
      });
    }
    // Also sets the region when the plugin is already installed.
    steps.push({ title: "Installing the Honeybadger plugin in Claude Code", cmd: install });
  }

  if (byId.codex?.bin) {
    // Codex also reads ~/.agents/skills, so the plugin would load the skills twice.
    steps.push({
      title: "Removing the Honeybadger plugin from Codex",
      cmd: ["codex", "plugin", "remove", PLUGIN],
      ignoreFailure: true,
    });
  }

  const shared = agents.filter((agent) => agent.skills);
  if (shared.length > 0) {
    steps.push({
      title: `Installing the Honeybadger skills for ${list(shared)}`,
      cmd: ["npx", "-y", SKILLS_CLI, "add", repoSource(env), "--global",
        "--agent", ...shared.map((agent) => agent.skills), "--skill", "*", "--yes"],
      // Don't send the skills CLI's usage data on our users' behalf
      env: { DISABLE_TELEMETRY: "1" },
    });
  }

  const mcp = agents.filter((agent) => agent.mcp);
  if (mcp.length > 0) {
    steps.push({
      title: `Adding ${server} to ${list(mcp)}`,
      mcp: mcp.map((agent) => agent.mcp),
      url,
    });
  }

  if (byId.other) {
    steps.push({
      title: `Add ${server} to your other agent`,
      // The common mcpServers format; agents with their own format (OpenCode's `mcp`, for one) need their docs
      snippet: JSON.stringify({ mcpServers: { honeybadger: { type: "http", url } } }, null, 2),
      url,
    });
  }

  if (byId.amp && !byId.amp.bin) {
    steps.push({
      title: `Add ${server} to Amp`,
      manual: [["amp", "mcp", "add", "honeybadger", url]],
    });
  } else if (byId.amp) {
    steps.push(
      {
        title: "Removing an existing honeybadger MCP server from Amp",
        cmd: ["amp", "mcp", "remove", "honeybadger"],
        ignoreFailure: true,
      },
      {
        title: `Adding ${server} to Amp`,
        cmd: ["amp", "mcp", "add", "honeybadger", url],
      },
    );
  }

  return steps;
}

function list(agents) {
  return new Intl.ListFormat("en").format(agents.map((agent) => agent.listName ?? agent.name));
}
