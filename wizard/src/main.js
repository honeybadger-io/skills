import { homedir } from "node:os";
import { parseArgs } from "node:util";
import * as p from "@clack/prompts";
import spawn from "cross-spawn";
import { AGENTS, PROMPT, findAgent, plan } from "./agents.js";
import {
  addMcpServer,
  copySkills,
  findBin,
  looksLikeProject,
  removeSkills,
  skillsSource,
} from "./install.js";

const IDS = AGENTS.map((agent) => agent.id).join(", ");

const HELP = `Set up Honeybadger with your coding agent.

Installs the Honeybadger skills and MCP server for your coding agents, then
starts one to add Honeybadger to the app in this directory.

Usage: npx @honeybadger-io/wizard [options]

Options:
  --agent <id>       Agent to set up; repeat for more than one (default: ask)
                     ${IDS}
  --region <us|eu>   Honeybadger region (default: ask)
  --no-launch        Install only; don't start an agent
  --dry-run          Print what would run, change nothing
  -y, --yes          Don't ask: set up every agent on your PATH and start the first
  -h, --help         Show this help
`;

const MANUAL = `Install a supported agent's CLI and run this again, or set up your
agent by hand: https://github.com/honeybadger-io/skills#install`;

export async function main(argv) {
  try {
    return await wizard(argv);
  } catch (err) {
    if (!(err instanceof NoTerminal)) throw err;
    p.log.error("No terminal to ask in. Pass --region, plus --agent or --yes.");
    return stop("Setup cancelled.", 1);
  }
}

async function wizard(argv) {
  let args;
  try {
    ({ values: args } = parseArgs({
      args: argv,
      options: {
        agent: { type: "string", multiple: true },
        region: { type: "string" },
        "no-launch": { type: "boolean" },
        "dry-run": { type: "boolean" },
        yes: { type: "boolean", short: "y" },
        help: { type: "boolean", short: "h" },
      },
    }));
  } catch (err) {
    console.error(`${err.message}\n\n${HELP}`);
    return 1;
  }
  if (args.help) {
    console.log(HELP);
    return 0;
  }
  const requested = (args.agent ?? []).flatMap((value) => value.split(","));
  const unknown = requested.find((id) => !findAgent(id));
  if (unknown) {
    console.error(`Unknown agent "${unknown}". Use one of: ${IDS}.`);
    return 1;
  }
  if (args.region && !["us", "eu"].includes(args.region)) {
    console.error(`Unknown region "${args.region}". Use us or eu.`);
    return 1;
  }
  const dryRun = args["dry-run"];
  const yes = args.yes;

  p.intro("Honeybadger setup");

  if (!looksLikeProject(process.cwd()) && !yes) {
    p.log.warn("This doesn't look like an app directory.");
    const go = await ask(() =>
      p.confirm({ message: "Set up Honeybadger here anyway?", initialValue: false }),
    );
    if (!go) return stop("Run the wizard again from your app's directory.");
  }

  const changes = uncommittedChanges();
  if (changes.length > 0 && !yes) {
    const shown = changes.slice(0, 10).join("\n");
    const more = changes.length > 10 ? `\n...and ${changes.length - 10} more` : "";
    p.log.warn(
      `You have uncommitted changes. Your agent will edit files here, so commit or stash them first to review its changes on their own.\n${shown}${more}`,
    );
    const go = await ask(() => p.confirm({ message: "Continue anyway?", initialValue: false }));
    if (!go) return stop("Commit or stash your changes, then run the wizard again.");
  }

  // Pick the agents. Ones with their CLI on PATH start checked; the others
  // still work, they just can't be started for you.
  const all = AGENTS.map((agent) => ({ ...agent, bin: findBin(agent.bins) }));
  const installed = all.filter((agent) => agent.bin);
  let agents;
  if (requested.length > 0) {
    agents = all.filter((agent) => requested.includes(agent.id));
  } else if (yes) {
    if (installed.length === 0) {
      p.log.error(`Couldn't find a supported agent's CLI on your PATH. Pass --agent to pick one.`);
      return stop(MANUAL, 1);
    }
    agents = installed;
    p.log.info(`Setting up ${agents.map((a) => a.name).join(", ")}.`);
  } else {
    const ids = await ask(() =>
      p.multiselect({
        message: "Which agents should get Honeybadger?",
        options: all.map((a) => ({
          value: a.id,
          label: a.name,
          hint: a.bin ? undefined : "not found on PATH",
        })),
        initialValues: installed.map((a) => a.id),
        required: true,
      }),
    );
    if (ids === undefined) return stop();
    agents = all.filter((a) => ids.includes(a.id));
  }

  // Pick the region.
  const region =
    args.region ??
    (await ask(() =>
      p.select({
        message: "Which Honeybadger region is your account in?",
        options: [
          { value: "us", label: "US", hint: "app.honeybadger.io, the default" },
          { value: "eu", label: "EU", hint: "eu-app.honeybadger.io" },
        ],
      }),
    ));
  if (region === undefined) return stop();

  // Install.
  const manual = [];
  for (const step of plan(agents, region, homedir())) {
    if (step.manual) {
      manual.push(step);
      continue;
    }
    if (dryRun) {
      p.log.step(`${step.title}\n${describe(step)}`);
      continue;
    }
    const spin = p.spinner();
    spin.start(step.title);
    try {
      run(step);
      spin.stop(step.title);
    } catch (err) {
      if (step.ignoreFailure) {
        spin.clear();
        continue;
      }
      spin.error(step.title);
      p.log.error(err.message);
      return stop("Setup didn't finish. Fix the error above and run the wizard again.", 1);
    }
  }
  for (const agent of agents) {
    if (agent.note) p.log.warn(agent.note);
  }
  for (const step of manual) {
    p.note(step.manual.map(quote).join(" "), `${step.title} by running`);
  }

  if (dryRun) {
    showPrompt(agents);
    p.outro("Dry run: nothing was changed.");
    return 0;
  }

  // Start an agent, or say how to.
  const agent = await pickLaunch(agents, { skip: args["no-launch"], yes });
  if (!agent) {
    showPrompt(agents);
    p.outro("Honeybadger is installed.");
    return 0;
  }
  p.outro(`Starting ${agent.name}. When it asks, log in to Honeybadger in your browser.`);
  const result = spawn.sync(agent.bin, agent.launch(PROMPT), { stdio: "inherit" });
  return result.status ?? 1;
}

/** Returns the agent to start, or undefined to print the prompt instead. */
async function pickLaunch(agents, { skip, yes }) {
  const launchable = agents.filter((agent) => agent.bin && agent.launch);
  if (skip || launchable.length === 0 || !process.stdin.isTTY) return undefined;
  if (yes) return launchable[0];
  if (launchable.length === 1) {
    const go = await ask(() =>
      p.confirm({ message: `Start ${launchable[0].name} to add Honeybadger to this app?` }),
    );
    return go ? launchable[0] : undefined;
  }
  const id = await ask(() =>
    p.select({
      message: "Start an agent to add Honeybadger to this app?",
      options: [
        ...launchable.map((a) => ({ value: a.id, label: `Start ${a.name}` })),
        { value: "none", label: "No, I'll start one myself" },
      ],
    }),
  );
  return launchable.find((a) => a.id === id);
}

function showPrompt(agents) {
  const [agent] = agents;
  if (agents.length === 1 && agent.bin && agent.launch) {
    p.note(`${agent.bin} ${agent.launch(PROMPT).map(quote).join(" ")}`, "Start your agent with");
  } else {
    const names = new Intl.ListFormat("en", { type: "disjunction" }).format(
      agents.map((a) => a.name),
    );
    p.note(PROMPT, `Start ${names} in this directory and ask`);
  }
}

class NoTerminal extends Error {}

/** Runs a prompt; returns undefined if the user cancels (Ctrl-C). */
async function ask(prompt) {
  if (!process.stdin.isTTY) throw new NoTerminal();
  const answer = await prompt();
  return p.isCancel(answer) ? undefined : answer;
}

function stop(message = "Setup cancelled.", code = 0) {
  p.cancel(message);
  return code;
}

/** `git status --porcelain` lines, or none outside a git repo. */
function uncommittedChanges() {
  const result = spawn.sync("git", ["status", "--porcelain"], { encoding: "utf8" });
  if (result.status !== 0) return [];
  return result.stdout.split("\n").filter(Boolean);
}

function run(step) {
  if (step.cmd) {
    const [bin, ...rest] = step.cmd;
    const result = spawn.sync(bin, rest, { encoding: "utf8" });
    if (result.error) throw result.error;
    if (result.status !== 0) {
      const output = (result.stderr || result.stdout || "").trim();
      throw new Error(`\`${step.cmd.join(" ")}\` failed${output ? `:\n${output}` : "."}`);
    }
  } else if (step.copySkills) {
    copySkills(skillsSource(), step.copySkills);
  } else if (step.removeSkills) {
    removeSkills(step.removeSkills);
  } else if (step.mcp) {
    addMcpServer(step.mcp, step.url);
  }
}

function describe(step) {
  if (step.cmd) return `  $ ${step.cmd.map(quote).join(" ")}`;
  if (step.copySkills) return `  copy honeybadger-* skills to ${step.copySkills}`;
  if (step.removeSkills) return `  remove honeybadger-* skills from ${step.removeSkills}`;
  return `  add-mcp: honeybadger = ${step.url} for ${step.mcp.join(", ")}`;
}

function quote(arg) {
  return /^[\w@%+=:,./-]+$/.test(arg) ? arg : `"${arg.replaceAll('"', '\\"')}"`;
}
