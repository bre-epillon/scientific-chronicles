const fs = require("fs");
const path = require("path");
const { execFileSync } = require("child_process");

const moduleConfigPath = path.join(
  __dirname,
  "..",
  "config",
  "_default",
  "module.toml",
);

function parseVersion(version) {
  return version.split(".").map((part) => Number.parseInt(part, 10));
}

function compareVersions(left, right) {
  const a = parseVersion(left);
  const b = parseVersion(right);

  for (let i = 0; i < Math.max(a.length, b.length); i += 1) {
    const diff = (a[i] || 0) - (b[i] || 0);
    if (diff !== 0) {
      return diff;
    }
  }

  return 0;
}

function readSupportedRange() {
  const fallback = {
    extended: true,
    min: "0.151.0",
    max: "0.170.0",
  };

  try {
    const content = fs.readFileSync(moduleConfigPath, "utf8");
    const min = content.match(/^\s*min\s*=\s*"([^"]+)"/m)?.[1] || fallback.min;
    const max = content.match(/^\s*max\s*=\s*"([^"]+)"/m)?.[1] || fallback.max;
    const extended =
      content.match(/^\s*extended\s*=\s*(true|false)/m)?.[1] !== "false";

    return { min, max, extended };
  } catch {
    return fallback;
  }
}

function getInstalledHugo() {
  try {
    const output = execFileSync("hugo", ["version"], {
      cwd: path.join(__dirname, ".."),
      encoding: "utf8",
      stdio: ["ignore", "pipe", "pipe"],
    }).trim();

    const version = output.match(/hugo v(\d+\.\d+\.\d+)/)?.[1];
    const extended = output.includes("+extended");

    if (!version) {
      throw new Error(`Unable to parse Hugo version from: ${output}`);
    }

    return { output, version, extended };
  } catch (error) {
    const detail = error.stderr?.toString().trim() || error.message;
    console.error("Unable to run `hugo version`.");
    console.error(detail);
    process.exit(1);
  }
}

const supported = readSupportedRange();
const installed = getInstalledHugo();

const versionTooOld = compareVersions(installed.version, supported.min) < 0;
const versionTooNew = compareVersions(installed.version, supported.max) > 0;
const missingExtended = supported.extended && !installed.extended;

if (versionTooOld || versionTooNew || missingExtended) {
  console.error("Unsupported Hugo installation for this project.");
  console.error(`Installed: ${installed.version}${installed.extended ? " extended" : ""}`);
  console.error(
    `Required: ${supported.min} to ${supported.max}${supported.extended ? " extended" : ""}`,
  );
  console.error("");
  console.error("This theme uses newer Hugo features, including Tailwind CSS integration.");
  console.error("Update Hugo, then rerun the npm command.");
  process.exit(1);
}
