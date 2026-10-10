import { homedir } from "node:os";
import { parseArgs } from "node:util";
import * as p from "@clack/prompts";
import spawn from "cross-spawn";
import { AGENTS, PROMPT, findAgent } from "./agents.js";
import {
  addMcpServer,
  copySkills,
  findBin,
  looksLikeProject,
  skillsSource,
} from "./install.js";

const HELP = `Set up Honeybadger with your coding agent.

Installs the Honeybadger skills and MCP server for Claude Code, Codex, or
Cursor, then starts the agent to add Honeybadger to the app in this directory.

Usage: npx @honeybadger-io/wizard [options]

Options:
  --agent <claude|codex|cursor>  Agent to set up (default: ask)
  --region <us|eu>               Honeybadger region (default: ask)
  --no-launch                    Install only; don't start the agent
  --dry-run                      Print what would run, change nothing
  -h, --help                     Show this help
`;

const MANUAL = `Install one of Claude Code, Codex, or Cursor's CLI and run this again,
or set up your agent by hand: https://github.com/honeybadger-io/skills#install`;

export async function main(argv) {
  try {
    return await wizard(argv);
  } catch (err) {
    if (!(err instanceof NoTerminal)) throw err;
    p.log.error("No terminal to ask in. Pass --agent and --region.");
    return stop("Setup cancelled.", 1);
  }
}

async function wizard(argv) {
  let args;
  try {
    ({ values: args } = parseArgs({
      args: argv,
      options: {
        agent: { type: "string" },
        region: { type: "string" },
        "no-launch": { type: "boolean" },
        "dry-run": { type: "boolean" },
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
  if (args.agent && !findAgent(args.agent)) {
    console.error(`Unknown agent "${args.agent}". Use claude, codex, or cursor.`);
    return 1;
  }
  if (args.region && !["us", "eu"].includes(args.region)) {
    console.error(`Unknown region "${args.region}". Use us or eu.`);
    return 1;
  }
  const dryRun = args["dry-run"];
  const launch = !args["no-launch"];

  p.intro("Honeybadger setup");

  if (!looksLikeProject(process.cwd())) {
    p.log.warn("This doesn't look like an app directory.");
    const go = await ask(() =>
      p.confirm({ message: "Set up Honeybadger here anyway?", initialValue: false }),
    );
    if (!go) return stop("Run the wizard again from your app's directory.");
  }

  // Pick the agent.
  const installed = AGENTS.map((agent) => ({ ...agent, bin: findBin(agent.bins) })).filter(
    (agent) => agent.bin,
  );
  let agent;
  if (args.agent) {
    agent = installed.find((a) => a.id === args.agent);
    if (!agent) {
      const { name, bins } = findAgent(args.agent);
      p.log.error(`${name} isn't installed (no ${bins.join(" or ")} on your PATH).`);
      return stop(MANUAL, 1);
    }
  } else if (installed.length === 0) {
    p.log.error("Couldn't find Claude Code, Codex, or Cursor's CLI on your PATH.");
    return stop(MANUAL, 1);
  } else if (installed.length === 1) {
    agent = installed[0];
    p.log.info(`Found ${agent.name}.`);
  } else {
    const id = await ask(() =>
      p.select({
        message: "Which agent should set up Honeybadger?",
        options: installed.map((a) => ({ value: a.id, label: a.name })),
      }),
    );
    if (id === undefined) return stop();
    agent = installed.find((a) => a.id === id);
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
  const steps = agent.steps(region, homedir());
  for (const step of steps) {
    if (dryRun) {
      p.log.step(`${step.title}\n${describe(step)}`);
      continue;
    }
    if (step.interactive) {
      p.log.step(`${step.title}. Log in to Honeybadger in your browser when it opens.`);
      const result = spawn.sync(step.cmd[0], step.cmd.slice(1), { stdio: "inherit" });
      if (result.status !== 0) {
        p.log.error(`\`${step.cmd.join(" ")}\` failed.`);
        return stop("Setup didn't finish. Fix the error above and run the wizard again.", 1);
      }
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

  if (!launch || dryRun) {
    p.note(`${agent.bin} "${PROMPT}"`, "Start your agent with");
    p.outro(dryRun ? "Dry run: nothing was changed." : "Honeybadger is installed.");
    return 0;
  }

  p.outro(
    `Starting ${agent.name}. When it asks, log in to Honeybadger in your browser.`,
  );
  const result = spawn.sync(agent.bin, [PROMPT], { stdio: "inherit" });
  return result.status ?? 1;
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
  } else if (step.mcpJson) {
    addMcpServer(step.mcpJson, step.url);
  }
}

function describe(step) {
  if (step.cmd) return `  $ ${step.cmd.join(" ")}`;
  if (step.copySkills) return `  copy honeybadger-* skills to ${step.copySkills}`;
  return `  set mcpServers.honeybadger.url = ${step.url} in ${step.mcpJson}`;
}
