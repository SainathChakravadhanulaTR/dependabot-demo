# Dependabot — Recommended Configuration for TR Repos

**Status:** Draft v0.1 — proposed standard
**Owner:** Sainath Chakravadhanula
**Last updated:** 2026-05-15

---

## Why this guide exists

Dependabot is GitHub's built-in tool for keeping dependencies fresh and
patched. It is free, organisation-wide, and the right answer to "how do we
stop letting CVEs sit unpatched for months?". Despite that, adoption across
TR repos is patchy, and the most common reasons teams cite are:

1. **"It generates too many PRs."** Engineers stop reviewing them; the noise
   defeats the purpose.
2. **"It breaks our build with major-version upgrades."** A team gets burned
   once, disables it, and never comes back.

Both complaints are real — but they are not flaws in Dependabot. They are
flaws in the *default* configuration. This guide documents the configuration
TR repos should adopt to make Dependabot quiet, safe, and worth keeping on.

---

## TL;DR

Drop the YAML in [the recommended configuration](#the-recommended-githubdependabotyml)
into `.github/dependabot.yml` of any repo. That single file does four things:

| Knob | What it does |
|---|---|
| `schedule: weekly` | One wave of PRs per week, not a daily drip. |
| `groups:` | All routine bumps for an ecosystem batch into **one** PR. |
| `ignore: version-update:semver-major` | Major-version bumps are excluded. Engineers plan those deliberately. |
| `open-pull-requests-limit:` | Hard cap on how many dependency PRs can stack up. |

Optionally, add the [auto-merge workflow](#enabling-auto-merge-for-safe-updates)
so that patch and minor updates land themselves once CI passes.

Security-update PRs (CVE-driven) intentionally **bypass** the schedule and the
PR limit. That's the behaviour we want — CVEs should never wait until Monday.

---

## The recommended `.github/dependabot.yml`

```yaml
version: 2

updates:
  # ---- Python (pip / requirements.txt) ----
  - package-ecosystem: "pip"
    directory: "/"
    schedule:
      interval: "weekly"
      day: "monday"
      time: "07:00"
      timezone: "Etc/UTC"
    open-pull-requests-limit: 5
    groups:
      python-minor-and-patch:
        update-types: ["minor", "patch"]
    ignore:
      - dependency-name: "*"
        update-types: ["version-update:semver-major"]
    labels: ["dependencies", "dependabot"]
    commit-message:
      prefix: "chore(deps)"
      include: "scope"

  # ---- GitHub Actions pinned versions ----
  - package-ecosystem: "github-actions"
    directory: "/"
    schedule:
      interval: "weekly"
      day: "monday"
    open-pull-requests-limit: 3
    groups:
      actions-minor-and-patch:
        update-types: ["minor", "patch"]
    ignore:
      - dependency-name: "*"
        update-types: ["version-update:semver-major"]
    labels: ["dependencies", "ci"]
```

For repos that use other package managers, add another block per ecosystem
following the same shape (see [Adding more ecosystems](#adding-more-ecosystems)).

---

## What each setting does and why we picked it

| Setting | Value | Why this value |
|---|---|---|
| `schedule.interval` | `weekly` | Daily produces a constant trickle that engineers learn to ignore. Monthly leaves CVE-adjacent patches sitting for too long. Weekly is the sweet spot — predictable, scannable, frequent enough that the queue never grows. |
| `schedule.day` + `time` | Monday 07:00 UTC | PRs arrive at the start of the work week. Teams can budget 30 minutes on Monday morning instead of context-switching mid-week. |
| `groups` | All `minor` + `patch` in one group per ecosystem | Without grouping, 8 patch bumps = 8 PRs. With grouping, 8 patch bumps = 1 PR with a combined diff. This is the single biggest noise reducer. |
| `ignore: version-update:semver-major` | `*` (all packages) | Majors are breaking by convention. Auto-PR'ing them means engineers get blindsided. Excluding them does **not** mean we never upgrade majors — it means we do them on our schedule, with a test plan. |
| `open-pull-requests-limit` | 5 for pip, 3 for actions | A hard ceiling so even if grouping misfires, the queue never explodes. |
| `labels` | `dependencies`, `dependabot` (+ `ci` for actions) | Lets teams filter the PR list, build dashboards, or route Dependabot PRs to a specific review channel. |
| `commit-message.prefix` | `chore(deps)` | Plays nicely with conventional commits if the repo uses them. Harmless if it doesn't. |

> **Why not just turn off major-version updates** *via* a UI toggle?
> Dependabot has no such toggle. The only way to filter major bumps out is
> the `ignore` block above. This is why every repo needs the YAML file —
> there is no point-and-click equivalent.

---

## Adding more ecosystems

The above example covers Python and GitHub Actions. Repos using other
package managers should add another `- package-ecosystem:` block with the
same `schedule`, `groups`, `ignore`, and `open-pull-requests-limit` shape.
Supported ecosystem values:

| Repo uses | `package-ecosystem:` value |
|---|---|
| `package.json` / npm / yarn | `npm` |
| `pom.xml` / Gradle | `maven` or `gradle` |
| `*.csproj` / NuGet | `nuget` |
| `go.mod` | `gomod` |
| `Dockerfile` | `docker` |
| `Gemfile` | `bundler` |
| `Cargo.toml` | `cargo` |
| Terraform modules | `terraform` |

A repo with three of these gets three blocks in `dependabot.yml`. The
*strategy* — weekly, grouped, no majors, capped — is uniform across all of
them.

---

## Enabling auto-merge for safe updates

This is opt-in. If you want patch and minor PRs to merge themselves once CI
passes (so engineers only review majors and CVE PRs), add this workflow:

```yaml
# .github/workflows/dependabot-auto-merge.yml
name: Dependabot auto-merge

on: pull_request_target

permissions:
  contents: write
  pull-requests: write

jobs:
  automerge:
    if: github.actor == 'dependabot[bot]'
    runs-on: ubuntu-latest
    steps:
      - uses: dependabot/fetch-metadata@v2
        id: meta
      - if: |
          steps.meta.outputs.update-type == 'version-update:semver-patch' ||
          steps.meta.outputs.update-type == 'version-update:semver-minor'
        run: gh pr merge --auto --squash "$PR_URL"
        env:
          PR_URL: ${{ github.event.pull_request.html_url }}
          GH_TOKEN: ${{ secrets.GITHUB_TOKEN }}
```

For this workflow to actually merge anything, **three repo-level settings**
also need to be on (the YAML alone isn't enough — GitHub deliberately gates
auto-merge behind a repo-level opt-in):

1. **Settings → General → Pull Requests**: enable **"Allow auto-merge"**.
2. **Settings → Actions → General → Workflow permissions**: select **"Read
   and write permissions"** and tick **"Allow GitHub Actions to create and
   approve pull requests"**.
3. **Settings → Branches → Add ruleset** on `main`: require the CI status
   check to pass before merging. (Without a required check, GitHub treats
   PRs as instantly mergeable and the auto-merge button stays disabled —
   there's nothing for it to wait on.)

### Conservative variant — auto-merge patch only

Some teams prefer to auto-merge only patch versions (e.g. 1.2.3 → 1.2.4) and
review minors manually, on the principle that not every library follows
semver strictly. To do that, drop the `semver-minor` clause from the `if:`
in the workflow above. This is a per-repo decision; both are defensible.

---

## What teams should expect week-to-week

Once this is wired up, the operating model is:

- **Monday morning** — one batched PR per ecosystem appears (e.g. one for
  Python, one for GitHub Actions). Each contains the week's collected
  minor/patch bumps with a combined changelog summary.
- **If auto-merge is on** — CI runs, those PRs merge themselves, and no one
  has to look at them unless CI fails.
- **If auto-merge is off** — a reviewer scans the diff (usually 30 seconds
  per ecosystem), clicks merge, done.
- **At any time** — CVE security-update PRs land immediately. These are
  outside the weekly schedule and outside the PR cap. Treat them as priority.
- **Quarterly** — a designated owner reviews the list of *suppressed*
  major-version updates and schedules deliberate upgrade work for any that
  matter. This prevents majors silently accumulating into a "we're now five
  major versions behind on everything" situation.

That last bullet is the discipline this guide depends on. Ignoring majors
is only safe if someone is *actually* tracking them and planning upgrades.
We are not deferring forever; we are deferring to a planned cadence.

---

## Anti-patterns — what NOT to do

| Anti-pattern | Why it's bad |
|---|---|
| Enable Dependabot via the UI without committing `dependabot.yml` | You get the noisy daily defaults. This is what burns teams. |
| Use `schedule: interval: daily` | A daily drip is the #1 cause of "I stopped looking at Dependabot PRs." |
| Skip the `groups` block | One PR per package per week is still 12 PRs/week in a typical repo. Group them. |
| Auto-merge majors | Defeats the entire point of the major-version ignore rule. |
| Ignore *all* updates, not just majors | You'll stop getting security patches. CVE PRs will still come through, but version drift will accumulate silently. |
| Set `open-pull-requests-limit: 99` | If you need a cap that high, your grouping isn't working. Fix the cause, not the symptom. |
| Hardcode individual reviewer GitHub handles in `dependabot.yml` | Use `CODEOWNERS` for reviewer routing instead — it survives people changing teams. |

---

## Recommended TR rollout

1. **Pilot (now → +2 weeks).** Apply this config to 2–3 volunteer repos
   across different stacks (one Python, one Node, one .NET if possible).
   Capture the first month of PRs — volume, what got auto-merged, what
   broke. This produces the "evidence" version of this guide.
2. **Publish the standard (week 3).** Once the pilots hold up, this MD file
   becomes the canonical reference, linked from the engineering wiki.
3. **Make it the new-repo default (week 4+).** TR's org-level `.github`
   template repo should ship with `dependabot.yml` pre-populated, so any
   new repo created from a template has the standard from day one. Existing
   repos opt in by copying the file.
4. **Owners.** A small group (2–3 people across security + platform)
   maintains this guide and answers escalations. Not a dedicated team — a
   shared responsibility.

---

## FAQ

**Q: Will this catch zero-day CVEs the day they're disclosed?**
Yes. Security-update PRs are independent of the weekly schedule and
independent of the PR limit. They fire as soon as Dependabot's advisory
database picks up the CVE — typically within hours of disclosure.

**Q: What if a minor-version update breaks CI?**
The PR sits there, unmerged, with a red status check. The team sees it on
Monday morning during their normal triage. Auto-merge does not fire on red
CI. There is no automated harm.

**Q: Can we skip Dependabot and use Renovate / Snyk / something else?**
Renovate is more configurable, Snyk has nicer reporting, both are valid.
The argument for Dependabot is that it's free, native to GitHub, requires
no third-party app installation, and the config above closes most of the
"Renovate is better" gap. Start with Dependabot; revisit if a real
capability gap appears.

**Q: What about lockfiles (`package-lock.json`, `Pipfile.lock`)?**
Dependabot updates them automatically as part of the same PR. No extra
config.

**Q: What if a repo has multiple sub-projects (monorepo)?**
Add one `- package-ecosystem:` block per `directory:`. Same ecosystem can
appear multiple times with different paths.

**Q: How do we measure whether this is working?**
Two metrics matter:
1. **Time-to-patch on CVEs** — measured from advisory publication to PR
   merge. Target: < 7 days for high/critical.
2. **PR review burden** — how often engineers actually open and read a
   Dependabot PR. If auto-merge is on, this should be near-zero for routine
   weeks.

---

## Appendix: The reference implementation

The configuration in this guide is running in a sandbox repo with
deliberately outdated dependencies, so the behaviour can be observed on
real PRs rather than described abstractly. See the [`README`](./README.md)
in this repo for the demo walkthrough.
