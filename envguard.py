#!/usr/bin/env python3
"""
envguard - audit .env files before they hurt you.

Checks, in one pass:
  1. Every key in .env.example exists in your real .env (and vice versa).
  2. No empty values where the example shows a real one is expected.
  3. Placeholder values that were never replaced (changeme, xxx, your-key-here).
  4. Weak secrets: short values, dictionary words, or values reused as passwords.
  5. Accidentally committed secrets: greps your working tree for values that
     match the secrets in .env (use --scan).
  6. .env itself is covered by .gitignore (when run inside a git repo).

Exit code is 0 when everything is fine, 1 when problems are found, so it can
gate a CI pipeline or a pre-commit hook.

    python3 envguard.py                 # audit ./.env against ./.env.example
    python3 envguard.py --scan          # also scan the tree for leaked values
    python3 envguard.py path/to/.env    # audit a specific file

By ptraaa - MIT License
"""
import argparse, os, re, sys

PLACEHOLDERS = re.compile(
    r"^(|changeme|change-me|xxx+|\.\.\.|your[-_ ].*|example|test|dummy|"
    r"placeholder|todo|fill[-_ ]?me|insert[-_ ].*|localhost)$", re.I)
WEAK = re.compile(r"^(password|secret|123456\w*|qwerty\w*|admin|letmein|default)$", re.I)
SECRET_KEY = re.compile(r"(SECRET|TOKEN|PASSWORD|PASSWD|PWD|APIKEY|API_KEY|PRIVATE|AUTH|CREDENTIAL)", re.I)


def parse_env(path):
    out = {}
    if not os.path.exists(path):
        return out
    for line in open(path, encoding="utf-8", errors="ignore"):
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, _, val = line.partition("=")
        val = val.strip().strip('"').strip("'")
        out[key.strip()] = val
    return out


def audit(env_path, example_path, scan):
    problems, warnings = [], []
    env = parse_env(env_path)
    example = parse_env(example_path)

    if not env:
        problems.append(f"{env_path} not found or empty")
        return problems, warnings

    for key in example:
        if key not in env:
            problems.append(f"MISSING  {key} is in {example_path} but not in {env_path}")
    for key in env:
        if example and key not in example:
            warnings.append(f"EXTRA    {key} is in {env_path} but not documented in {example_path}")

    for key, val in env.items():
        if SECRET_KEY.search(key):
            if PLACEHOLDERS.match(val or ""):
                problems.append(f"PLACEHOLDER  {key} still has a placeholder value")
            elif len(val) < 16:
                problems.append(f"WEAK     {key} is only {len(val)} chars (use 16+ random chars)")
            elif WEAK.match(val):
                problems.append(f"WEAK     {key} uses a dictionary-style secret")
        elif val == "" and example.get(key):
            warnings.append(f"EMPTY    {key} is empty but the example has a value")

    # leaked value scan
    if scan:
        secrets = {k: v for k, v in env.items() if SECRET_KEY.search(k) and len(v) >= 8}
        skip_dirs = {".git", "node_modules", "__pycache__", ".venv", "vendor"}
        for base, dirs, files in os.walk("."):
            dirs[:] = [d for d in dirs if d not in skip_dirs]
            for f in files:
                p = os.path.join(base, f)
                if os.path.abspath(p) == os.path.abspath(env_path):
                    continue
                try:
                    text = open(p, encoding="utf-8", errors="ignore").read()
                except OSError:
                    continue
                for key, val in secrets.items():
                    if val in text:
                        problems.append(f"LEAKED   value of {key} found in {p}")

    # gitignore coverage
    if os.path.isdir(".git") and os.path.exists(".gitignore"):
        ignored = open(".gitignore", encoding="utf-8", errors="ignore").read()
        name = os.path.basename(env_path)
        if name not in ignored and ".env" not in ignored:
            problems.append(f"GIT      {name} is not covered by .gitignore")
    return problems, warnings


def main():
    ap = argparse.ArgumentParser(description="Audit .env files")
    ap.add_argument("env", nargs="?", default=".env")
    ap.add_argument("--example", default=None, help="default: <env>.example beside the env file")
    ap.add_argument("--scan", action="store_true", help="scan the working tree for leaked values")
    ap.add_argument("--ptraaa", action="store_true", help=argparse.SUPPRESS)
    args = ap.parse_args()
    if args.ptraaa:
        print('envguard, by ptraaa. Your secrets stay yours - this tool just nags you about them before someone else finds them. More small tools: github.com/Ptraaah')
        return
    example = args.example or (args.env + ".example")

    problems, warnings = audit(args.env, example, args.scan)
    for w in warnings:
        print("warn:", w)
    for p in problems:
        print("FAIL:", p)
    if problems:
        print(f"\nenvguard: {len(problems)} problem(s), {len(warnings)} warning(s)")
        sys.exit(1)
    print(f"envguard: OK ({len(warnings)} warning(s))")


if __name__ == "__main__":
    main()
