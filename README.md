# dependabot-demo

A throwaway proof-of-concept repo that demonstrates a **best-practice
Dependabot configuration** for Thomson Reuters repos. The goal is to show, on
real PRs, that the two common complaints about Dependabot — *"too noisy"* and
*"breaks things with major bumps"* — are config problems, not Dependabot
problems.

---

## What this repo demonstrates

| Concern | How it's solved here | Where to look |
|---|---|---|
| Too many PRs | Weekly schedule + grouping (one PR per ecosystem, not one per package) | `.github/dependabot.yml` → `schedule.interval`, `groups` |
| Major-version breaking changes | Major bumps are explicitly ignored | `.github/dependabot.yml` → `ignore: version-update:semver-major` |
| Runaway PR queue | Hard cap on concurrent open PRs | `.github/dependabot.yml` → `open-pull-requests-limit` |
| Manual review of trivial bumps | Patch/minor auto-merge once CI is green | `.github/workflows/dependabot-auto-merge.yml` |
| CVEs in dependencies | Security-update PRs fire immediately, bypass the schedule and PR limit | GitHub Security tab on the repo |

The `requirements.txt` and the GitHub Actions workflow are **intentionally
pinned to old versions** so that Dependabot has something to do on the very
first scheduled run.

---

## How to spin up the demo

```powershell
# 1. Create the empty GitHub repo (UI or gh CLI) under your personal account,
#    e.g. https://github.com/SainathChakravadhanulaTR/dependabot-demo
#    DO NOT initialize it with a README — we already have one.

# 2. Wire up the remote and push:
git remote add origin https://github.com/SainathChakravadhanulaTR/dependabot-demo.git
git push -u origin main

# 3. On the repo's GitHub page:
#    Settings -> Code security and analysis -> enable:
#      - Dependency graph
#      - Dependabot alerts
#      - Dependabot security updates
#    (Version updates are enabled automatically by the presence of
#     .github/dependabot.yml — no UI toggle needed.)

# 4. (Optional but recommended for the auto-merge demo)
#    Settings -> General -> "Allow auto-merge" -> ON
#    Settings -> Branches -> add a protection rule on `main`:
#      - Require a pull request before merging
#      - Require status checks (select the CI workflow)
```

---

## What you should see after pushing

**Within ~10 minutes** of the first push:

1. **Security tab → Dependabot alerts** populates with CVEs for the
   intentionally outdated packages (`pyyaml 5.4.1`, `urllib3 1.26.5`, etc.).
2. **Pull requests tab** shows Dependabot opening **security update PRs**
   immediately for any package with a fixable CVE — these do *not* wait for
   Monday.

**On the next Monday 07:00 UTC tick** (or you can force it: see below):

3. A single grouped PR titled something like
   `chore(deps): bump the python-minor-and-patch group with N updates`
   appears, batching all minor/patch bumps for the Python packages.
4. A separate grouped PR for the `github-actions` ecosystem batching the
   `actions/checkout` and `actions/setup-python` minor/patch bumps.
5. **No major-version PRs** — even though e.g. `requests` has a major
   release available, it stays filtered out.

### Forcing a Dependabot run (so you don't have to wait until Monday)

On the repo page: **Insights → Dependency graph → Dependabot → "Check for
updates"** next to each ecosystem. This runs the same job on demand and is
the easiest way to demo to a manager.

---

## Talking points for the demo

When showing this to your manager:

1. Open the **Pull requests** tab → point at the single grouped PR. *"This
   is six dependency bumps in one PR instead of six PRs. That's the
   `groups:` block in `dependabot.yml`."*
2. Open the **Security** tab → point at the CVE alerts and the
   corresponding security-update PRs. *"Security PRs ignore the weekly
   schedule and the open-PR cap — they fire immediately, which is what we
   want."*
3. Open `.github/dependabot.yml` → walk through the four knobs (`schedule`,
   `groups`, `ignore`, `open-pull-requests-limit`) and show that each one
   maps to a specific complaint we'd hear about Dependabot defaults.
4. Open a Dependabot PR → show that CI ran and the PR was auto-merged
   (after `Allow auto-merge` is enabled). *"Engineers don't have to click
   anything for safe bumps."*

---

## Promoting this to a TR-wide template

Once this demo holds up, the same `.github/dependabot.yml` and
`dependabot-auto-merge.yml` can be dropped into any TR repo. The only
per-repo changes are:

- Add more `package-ecosystem:` blocks for whatever the repo actually
  uses (`npm`, `maven`, `nuget`, `docker`, `gomod`, etc.).
- Set `reviewers:` to the owning team's GitHub slug.
- Adjust `open-pull-requests-limit` per repo size if needed.

Everything else — the schedule, the grouping strategy, the
`semver-major` ignore — is the standard and shouldn't vary per repo.
