---
description: Safely prepare, validate, commit and push projects to GitHub while preventing secrets and unnecessary files from being uploaded.
---

# Professional GitHub Workflow

## Repository Detection

Before any git operation:

- Check if the current directory is a git repository.
- If not initialized:
  - Initialize git.
  - Create a professional .gitignore.
  - Review files before first commit.

## Sensitive Data Protection

Before every commit:

- Inspect for:
  - API keys
  - Tokens
  - Passwords
  - Connection strings
  - .env files
  - Private certificates
  - Local database files
  - Secrets in source code
  - Large files (>50MB)
  - Datasets
  - Backups
  - Videos
  - Archives (.zip, .rar, .7z)

- Never commit sensitive information.
- If sensitive data is detected:
  - Stop.
  - Report findings.
  - Suggest remediation.

## Professional Git Ignore

Ensure appropriate exclusions:

- .env
- .env.*
- node_modules
- dist
- build
- .venv
- __pycache__
- *.log
- *.db
- IDE folders
- OS files

Adapt exclusions to the project technology.

## Commit Quality

Use professional commit messages.

Format:

type(scope): short description

Examples:

feat(auth): add login validation
fix(api): handle timeout errors
docs(readme): update installation guide
refactor(users): simplify repository layer

Avoid generic commit messages.

## Commit Scope

Commit only relevant project files.

Never commit:

- temporary files
- cache files
- generated artifacts
- local configuration
- personal files

## Push Workflow

If repository exists:

- Pull latest changes first.
- Check for conflicts.
- Validate project state.
- Push only after verification.

If repository does not exist:

- Ask before creating remote repositories.

## Validation Before Push

Before push:

- Verify project builds successfully.
- Run available tests when appropriate.
- Verify no secrets are exposed.

Never push unverified code.

## Reporting

After git operations report only:

- repository status
- commit created
- files changed
- push result
- detected risks

## Execution Sequence

When this workflow is invoked:

1. Check git status.
2. Verify repository configuration.
3. Review .gitignore.
4. Detect sensitive files and secrets.
5. Review modified files.
6. Generate a professional commit message.
7. Show commit summary.
8. Show commit message and commit summary.
9. Ask for confirmation before committing.
10. Commit changes after confirmation.
11. Pull latest remote changes.
12. Resolve conflicts if any.
13. Push changes.
14. Report final status.## Safety Rules

Never push if:

- Secrets are detected.
- Build fails.
- Tests fail.
- Repository state is unclear.

Ask for confirmation before any destructive git operation.

Never push directly to protected branches unless explicitly requested.

Prefer:

- feature/*
- develop

Before pushing to main:
- Ask for confirmation.

## Invocation

When invoked without additional instructions:

- Automatically determine whether:
  - The repository is new.
  - The repository already exists.
  - Changes are pending.
  - A push is required.

Follow the appropriate workflow automatically.