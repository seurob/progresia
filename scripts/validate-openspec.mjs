import { existsSync, readdirSync, readFileSync, statSync } from "node:fs";
import { join } from "node:path";

const root = process.cwd();
const openspecDir = join(root, "openspec");
const requiredRootFiles = ["README.md", "project.yaml"];
const requiredDirs = ["specs", "changes"];
const requiredChangeFiles = ["proposal.md", "design.md", "tasks.md"];

const errors = [];

function requirePath(path, message) {
  if (!existsSync(path)) {
    errors.push(message);
  }
}

function listDirs(path) {
  if (!existsSync(path)) {
    return [];
  }

  return readdirSync(path)
    .map((name) => join(path, name))
    .filter((entry) => statSync(entry).isDirectory());
}

function listFilesRecursive(path) {
  if (!existsSync(path)) {
    return [];
  }

  return readdirSync(path).flatMap((name) => {
    const entry = join(path, name);
    return statSync(entry).isDirectory() ? listFilesRecursive(entry) : [entry];
  });
}

requirePath(openspecDir, "Missing openspec/ directory.");

for (const file of requiredRootFiles) {
  requirePath(join(openspecDir, file), `Missing openspec/${file}.`);
}

for (const dir of requiredDirs) {
  requirePath(join(openspecDir, dir), `Missing openspec/${dir}/ directory.`);
}

const baseSpecFiles = listFilesRecursive(join(openspecDir, "specs")).filter((file) =>
  file.endsWith("spec.md")
);

if (baseSpecFiles.length === 0) {
  errors.push("Missing at least one base spec under openspec/specs/**/spec.md.");
}

const changes = listDirs(join(openspecDir, "changes"));

if (changes.length === 0) {
  errors.push("Missing at least one change under openspec/changes/.");
}

for (const changeDir of changes) {
  const changeName = changeDir.split(/[\\/]/).at(-1);

  for (const file of requiredChangeFiles) {
    const filePath = join(changeDir, file);
    requirePath(filePath, `Missing ${changeName}/${file}.`);

    if (existsSync(filePath) && readFileSync(filePath, "utf8").trim().length === 0) {
      errors.push(`${changeName}/${file} is empty.`);
    }
  }

  const deltaSpecs = listFilesRecursive(join(changeDir, "specs")).filter((file) =>
    file.endsWith("spec.md")
  );

  if (deltaSpecs.length === 0) {
    errors.push(`Missing spec delta under ${changeName}/specs/**/spec.md.`);
  }

  for (const specFile of deltaSpecs) {
    const content = readFileSync(specFile, "utf8");

    if (!content.includes("## ADDED Requirements") && !content.includes("## MODIFIED Requirements")) {
      errors.push(`${specFile} must include ADDED or MODIFIED Requirements.`);
    }
  }
}

if (errors.length > 0) {
  console.error("OpenSpec validation failed:");
  for (const error of errors) {
    console.error(`- ${error}`);
  }
  process.exit(1);
}

console.log(`OpenSpec validation passed: ${baseSpecFiles.length} base spec(s), ${changes.length} change(s).`);
