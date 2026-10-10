import { join } from "node:path";

export const MCP_URLS = {
  us: "https://mcp.honeybadger.io/mcp",
  eu: "https://eu-mcp.honeybadger.io/mcp",
};

export const REPO = "honeybadger-io/skills";
export const PLUGIN = "honeybadger@honeybadger";

// Plain English instead of a slash command, so it works the same in every agent.
export const PROMPT =
  "Use the honeybadger-get-started skill to set up Honeybadger in this project.";

/**
 * A step is one of:
 *   { title, cmd: [bin, ...args], ignoreFailure?, interactive? }
 *                                                  - run a command (in the foreground
 *                                                    if it needs the user)
 *   { title, copySkills: dir }                     - copy the honeybadger-* skills into dir
 *   { title, mcpJson: file, url }                  - add the MCP server to a JSON config
 *
 * The US region installs each agent's plugin, which bundles the US MCP server.
 * The plugins can't point at the EU server, so EU installs remove the plugin if
 * it's there, copy the skills, and register the EU server directly.
 */
export const AGENTS = [
  {
    id: "claude",
    name: "Claude Code",
    bins: ["claude"],
    steps(region, home) {
      if (region === "us") {
        return [
          {
            title: "Adding the Honeybadger marketplace",
            cmd: ["claude", "plugin", "marketplace", "add", REPO],
          },
          {
            title: "Installing the Honeybadger plugin",
            cmd: ["claude", "plugin", "install", PLUGIN],
          },
        ];
      }
      return [
        {
          title: "Removing the US Honeybadger plugin",
          cmd: ["claude", "plugin", "uninstall", PLUGIN],
          ignoreFailure: true,
        },
        {
          title: "Installing the Honeybadger skills",
          copySkills: join(home, ".claude", "skills"),
        },
        {
          title: "Removing an existing honeybadger MCP server",
          cmd: ["claude", "mcp", "remove", "--scope", "user", "honeybadger"],
          ignoreFailure: true,
        },
        {
          title: "Adding the EU MCP server",
          cmd: [
            "claude", "mcp", "add", "--scope", "user", "--transport", "http",
            "honeybadger", MCP_URLS.eu,
          ],
        },
      ];
    },
  },
  {
    id: "codex",
    name: "Codex",
    bins: ["codex"],
    steps(region, home) {
      if (region === "us") {
        return [
          {
            title: "Adding the Honeybadger marketplace",
            cmd: ["codex", "plugin", "marketplace", "add", REPO],
          },
          {
            title: "Installing the Honeybadger plugin",
            cmd: ["codex", "plugin", "add", PLUGIN],
          },
        ];
      }
      return [
        {
          title: "Removing the US Honeybadger plugin",
          cmd: ["codex", "plugin", "remove", PLUGIN],
          ignoreFailure: true,
        },
        {
          title: "Installing the Honeybadger skills",
          copySkills: join(home, ".agents", "skills"),
        },
        {
          title: "Removing an existing honeybadger MCP server",
          cmd: ["codex", "mcp", "remove", "honeybadger"],
          ignoreFailure: true,
        },
        {
          title: "Adding the EU MCP server",
          cmd: ["codex", "mcp", "add", "honeybadger", "--url", MCP_URLS.eu],
          // Codex logs in to the server as soon as it's added.
          interactive: true,
        },
      ];
    },
  },
  {
    id: "cursor",
    name: "Cursor",
    // The CLI was renamed from cursor-agent to agent.
    bins: ["agent", "cursor-agent"],
    steps(region, home) {
      // The Cursor CLI can't install plugins, so every region copies the skills.
      return [
        {
          title: "Installing the Honeybadger skills",
          copySkills: join(home, ".agents", "skills"),
        },
        {
          title: `Adding the ${region === "eu" ? "EU " : ""}MCP server`,
          mcpJson: join(home, ".cursor", "mcp.json"),
          url: MCP_URLS[region],
        },
      ];
    },
  },
];

export function findAgent(id) {
  return AGENTS.find((agent) => agent.id === id);
}
