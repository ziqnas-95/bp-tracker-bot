# Git Command Reference (bp-tracker-bot)

My own cheat sheet for the workflow I actually use on this project. Not exhaustive Git docs — just the commands I forget.

## Starting new work

Always branch from an up-to-date `main` before touching any files.

```bash
git checkout main
git pull
git checkout -b feat/short-description
```

Naming: `feat/...` for new features, `fix/...` for bug fixes, `docs/...` for docs-only changes (e.g. `feat/recent20`, `fix/timezone-bug`, `docs/readme-update`).

## Checking where I am

```bash
git status                  # what's changed, what's staged, what branch I'm on
git branch                  # list local branches, * marks the current one
git log --oneline -10       # last 10 commits, short form
git diff                    # unstaged changes, file by file
git diff src/bpbot/main.py  # unstaged changes in one file
```

**Before every commit**, run `git status` and eyeball the list. `.env` must never appear. If it does, stop and check `.gitignore` before going further.

```bash
git check-ignore -v .env    # confirms .env is ignored; should print a matching rule
```

## Committing

```bash
git add .                   # stage everything changed
git add path/to/file.py     # stage just one file
git commit -m "feat: short description of what changed"
```

Commit message prefixes I use: `feat:`, `fix:`, `docs:`, `chore:`, `refactor:`.

## Pushing and opening a PR

```bash
git push -u origin feat/short-description
```

`-u` only needed the first time on a new branch; after that, plain `git push` works. Then open the PR on GitHub and merge into `main` (repo won't let me push straight to `main`, which is intentional).

## After a PR is merged

```bash
git checkout main
git pull
git branch -d feat/short-description         # delete the local branch, now merged
git push origin --delete feat/short-description   # delete it on GitHub too (optional, GitHub often offers to do this on the PR page)
```

## Fixing mistakes

```bash
git commit --amend -m "corrected message"     # fix the last commit's message (only if not pushed yet)
git checkout -- path/to/file.py               # discard unstaged changes to one file
git reset --soft HEAD~1                       # undo the last commit but keep the changes staged
```

If I've already pushed and need to fix something, easier to just make a new commit than rewrite history:

```bash
git add .
git commit -m "fix: correct earlier mistake"
git push
```

## Stashing (rarely needed, but handy)

If I need to switch branches with uncommitted changes I'm not ready to commit:

```bash
git stash              # shelve current changes
git checkout main
# ... do something else ...
git checkout feat/short-description
git stash pop           # bring the changes back
```

## Checking a file's history

```bash
git log --oneline -- src/bpbot/config.py     # every commit that touched this file
git log -p -- src/bpbot/config.py            # same, with the actual diffs shown
```

## Confirming a secret never got committed

```bash
git log --all -- .env        # should return nothing, ever
```

If this ever returns something: the token/key inside is compromised. Revoke it (BotFather `/revoke`, rotate the Supabase service_role key) — deleting the commit afterward is not enough, since it may already be pushed to GitHub.

## Render-specific notes

- Merging into `main` triggers an automatic Render redeploy. No extra command needed.
- Changing an environment variable in the Render dashboard also redeploys on its own.
- If a Render deploy fails right after adding a new required setting in code, check the Render **Environment** tab — the variable is probably missing there.

## My actual day-to-day loop

```bash
git checkout main && git pull
git checkout -b feat/whatever

# ... make changes ...

uv run pytest -q
uv run ruff check --fix .
uv run ruff format .

git add .
git status        # .env must NOT appear — check every time
git commit -m "feat: whatever"
git push -u origin feat/whatever

# open PR on GitHub, merge into main
git checkout main && git pull
git branch -d feat/whatever
```