// The intro banner: the Honeybadger bolt and wordmark in the style of a 90s release info file,
// then a box with the release details.
import { WriteStream } from "node:tty";

const MARK = [
  "           sds.",
  "         s$\" \"` ,d",
  "       s$\"    ,d$`",
  "     s$\"    ,d$$` $b.",
  "   s$\"    ,d$$$$   \"$b.",
  " s$\"    ,d$$$$P      \"$b.",
  "$$b    '\"\"\"$$$$$$P`   ,$P",
  " 'q$s     ,$$$$P`   ,dP`",
  "   'q$s  ,$$$P`   ,dP`",
  "     'q` d$P`   ,dP`",
  "        dP`   ,dP`",
  "       '` ,dsdP`",
  "           '\"`",
];

// FIGlet's "slant" font
const WORDMARK = [
  "    __  __                       __              __               ",
  "   / / / /___  ____  ___  __  __/ /_  ____ _____/ /___ ____  _____",
  "  / /_/ / __ \\/ __ \\/ _ \\/ / / / __ \\/ __ `/ __  / __ `/ _ \\/ ___/",
  " / __  / /_/ / / / /  __/ /_/ / /_/ / /_/ / /_/ / /_/ /  __/ /    ",
  "/_/ /_/\\____/_/ /_/\\___/\\__, /_.___/\\__,_/\\__,_/\\__, /\\___/_/     ",
  "                       /____/                  /____/             ",
];

const COLORS = {
  truecolor: { orange: "\x1b[38;2;234;89;55m", dim: "\x1b[2m", reset: "\x1b[0m" },
  ansi256: { orange: "\x1b[38;5;167m", dim: "\x1b[2m", reset: "\x1b[0m" },
};

/**
 * "truecolor", "ansi256", or null for no color, from Node's own check, which honors FORCE_COLOR, NO_COLOR,
 * TERM and CI.
 */
export function colorSupport(env = process.env) {
  const depth = WriteStream.prototype.getColorDepth.call(null, env);
  if (depth >= 24) return "truecolor";
  if (depth >= 8) return "ansi256";
  return null;
}

/**
 * The banner for a terminal `columns` wide: the bolt beside the wordmark, or the wordmark alone when the
 * terminal is too narrow, or "" when even that doesn't fit.
 */
export function banner({ columns = 80, color = null, details = [] } = {}) {
  const c = COLORS[color] ?? { orange: "", dim: "", reset: "" };
  const markWidth = Math.max(...MARK.map((line) => line.length));
  const wordWidth = Math.max(...WORDMARK.map((line) => line.length));
  const gap = 4;
  let art;
  let width;
  if (columns >= markWidth + gap + wordWidth) {
    width = markWidth + gap + wordWidth;
    const top = Math.floor((MARK.length - WORDMARK.length) / 2) + 1;
    art = MARK.map((line, i) => {
      const word = WORDMARK[i - top];
      return word ? line.padEnd(markWidth + gap) + c.orange + word + c.reset : line;
    });
  } else if (columns >= wordWidth) {
    width = wordWidth;
    art = WORDMARK.map((line) => c.orange + line + c.reset);
  } else {
    return "";
  }
  const keyWidth = Math.max(...details.map(([key]) => key.length));
  const inner = width - 4;
  const row = ([key, value]) => {
    let text = `  ${key.padStart(keyWidth)} : ${value}`;
    if (text.length > inner - 2) text = text.slice(0, inner - 5) + "...";
    return `  :${text.padEnd(inner - 1)}:`;
  };
  const box = details.length
    ? ["", `  .${"-".repeat(inner - 1)}.`, ...details.map(row), `  \`${"-".repeat(inner - 1)}'`].map((line) =>
        line ? c.dim + line + c.reset : line,
      )
    : [];
  return [...art.map((line) => line.trimEnd()), ...box].join("\n") + "\n";
}
