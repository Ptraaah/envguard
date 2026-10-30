# envguard

Audit your `.env` files before they hurt you. One pass, standard library only, exit code you can gate CI on.

## What it catches

- Keys present in `.env.example` but missing from your real `.env` (and undocumented extras)
- Placeholder secrets that were never replaced: `changeme`, `your-key-here`, `xxx`, `todo`...
- Weak secrets: too short, dictionary-style, or reused password patterns
- Leaked values: with `--scan`, it greps your whole working tree for the actual secret values from `.env` appearing in code, docs, or anywhere else
- `.env` not covered by `.gitignore` inside a git repo

## Usage

```bash
python3 envguard.py                  # audit ./.env against ./.env.example
python3 envguard.py --scan           # also scan the tree for leaked values
python3 envguard.py config/.env      # audit a specific file
```

Output from a real run against a deliberately broken project:

```
FAIL: MISSING  MISSING_KEY is in .env.example but not in .env
FAIL: PLACEHOLDER  API_SECRET still has a placeholder value
FAIL: WEAK     JWT_SECRET is only 5 chars (use 16+ random chars)
envguard: 3 problem(s), 0 warning(s)
```

Exit code 0 means clean, 1 means problems, so it drops straight into a pre-commit hook or a CI step.

## Indonesian summary

Pemeriksa file .env: kunci yang hilang, secret placeholder yang belum diganti, secret lemah, nilai secret yang bocor ke file lain, dan .env yang belum masuk .gitignore. Murni Python standar, cocok buat gerbang CI.

## License

MIT. By ptraaa.
