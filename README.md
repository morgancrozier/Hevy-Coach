# Hevy-Coach

An unofficial companion to [Hevy](https://www.hevyapp.com/) that turns workout
history into a readable report: what changed, what needs attention, and what to
focus on next. Runs locally in a terminal, with optional Markdown/CSV exports,
OpenAI commentary, and email. Not affiliated with Hevy.

## See it first

This excerpt comes from the [generated demo report](examples/demo-report.md),
using five fictional workouts across four dates:

> **Latest:** Upper body · 2025-01-22 17:00 UTC
>
> **Bench Press (Barbell):** 50 kg × 10; 50 kg × 10; 50 kg × 10 →
> 50 kg × 11; 50 kg × 10; 50 kg × 10. Logged volume +50 kg·reps.
>
> **Observation:** Chest Supported Row: RPE recorded for 2/3 working sets;
> effort is uncertain.
>
> **Next focus — Bench Press:** Consider the smallest available step toward
> more load; then return to the lower end of the rep target.
> Target: 6–10 reps. Both sessions reached 10+ reps on every set at the same
> load with all RPE ≤ 8.

The full report includes the previous and current sets for each suggestion,
assistance-aware comparisons, and detailed session totals. It is useful without AI.

## Install and try offline

Use Python **3.11 or newer**. From a terminal:

```sh
git clone https://github.com/morgancrozier/Hevy-Coach.git
cd Hevy-Coach
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
python hevy_stats.py --demo
```

On Windows, create the environment with `py -3 -m venv .venv` and activate it
with `.venv\Scripts\Activate.ps1` in PowerShell before the final two commands.

Installation downloads dependencies. **The demo itself makes no network requests**,
loads only the synthetic fixture, and neither reads personal configuration/data
nor writes reports or state. Credentials and all other flags are ignored in demo
mode. Fixed fixture dates are intentionally unfiltered, so it works in future years.
The same report generator handles demo and real workouts.

## Use your history

Fetching requires a Hevy API key; Hevy currently restricts its public API to Pro
accounts. Get a key in [Hevy developer settings](https://hevy.com/settings?developer)
and see the [official API docs](https://api.hevyapp.com/docs/).

Copy env.example to .env **only if you do not already have a .env file**, then set
`HEVY_API_KEY`. Shell environment values take precedence over .env.

```sh
python hevy_stats.py validate
python hevy_stats.py both --days 90 --save-markdown --save-csv
```

`validate` checks local configuration only; it does not verify credentials or
contact services. `both` fetches a fresh snapshot into hevy_events.json and reports
on that snapshot. The default fetch window is 30 days, ending now in UTC. Generated
Markdown and CSV files go into the ignored reports/ directory when requested.

To work from a saved snapshot or an older Hevy events export without fetching:

```sh
python hevy_stats.py analyze --infile hevy_events.json --save-markdown
python hevy_stats.py export --infile hevy_events.json
```

`analyze` and `export` use all supplied history unless you specify `--days`.
Without `--ai` or `--email`, they make no network requests. `fetch` saves only the
snapshot. Use `--outfile` for a different fetch destination, `--output-dir` for
exports, and `python hevy_stats.py --help` for all options. Unlike older versions,
analysis no longer writes Markdown and CSV automatically.

## Optional AI and email

Both require explicit flags; credentials alone do not enable them.

| Feature | Environment settings | Command |
| --- | --- | --- |
| AI commentary | `OPENAI_API_KEY`; optional `OPENAI_MODEL` (default `gpt-4o-mini`) | `python hevy_stats.py analyze --ai` |
| Email | `EMAIL_USER`, `EMAIL_PASSWORD`; optional `TO_EMAIL` (defaults to sender), `SMTP_SERVER` (default `smtp.gmail.com`), `SMTP_PORT` (default `587`) | `python hevy_stats.py analyze --email` |

Email uses SMTP with STARTTLS; use the credentials your provider requires
(for example, an app password). `python hevy_stats.py --test-email` tests the SMTP
login without sending a message. Normal verification never runs this command.

AI receives only report facts and suggestions and is asked to explain them briefly.
It uses one Chat Completions request per run, with no retries. The default model
is unchanged; overrides must support the same API parameters. A failure leaves
the deterministic report intact. AI wording can still be wrong; check it against
the evidence. There is no learning over time or persistent AI memory.

Terminal, Markdown, and email reuse the same generated report. Requested email
failure exits nonzero. SMTP acceptance does not guarantee inbox delivery.
See [automation and data handling](AUTOMATION.md) before running on GitHub Actions.

## How suggestions work

Optionally copy rep_rules.example.py to rep_rules.local.py and customize exact
exercise names and rep ranges. Unknown targets produce observations and a request
to configure a target, not an assumed prescription. Existing rep_rules.py is
supported as a fallback; both personal configuration paths are ignored by Git.

Comparisons match exercise template ID and routine ID, falling back to exact
exercise name and workout title. Sessions retain their IDs and timestamps.
Progression uses two comparable sessions at the same positive logged load and
normal-set count, complete reps/RPE, and every set reaching the configured rep
ceiling with RPE at or below `PROGRESSION_RPE_CEILING` (default 8). Suggestions
state their evidence and limits; these heuristics are not validated coaching.

Volume is the sum of each working set's kg × reps. Assisted exercises show
assistance separately: reducing assistance increases resistance. Only whole-word
“assisted” and “counterweight” labels trigger detection; exact-name overrides in
`ASSISTED_EXERCISES` handle exceptions. “Chest Supported Row” is not assisted.
Bodyweight and missing load are not estimated. Warmups are excluded from analysis;
failure/drop sets appear in totals but block progression suggestions. CSV retains
all sets, notes, durations, and distances.

There are no letter grades or definitive recovery, technique, or injury-risk
judgments. Equipment changes, incomplete logging, and short history limit what
can be inferred. An optional [saved routine sequence](docs/CYCLICAL-ROUTINES.md)
can label the next configured workout, without guessing readiness.

## Privacy, maintenance, and contributing

Raw history stays in local JSON unless you run on a remote runner. Exports may
contain workout notes. `--ai` sends report facts to OpenAI; `--email` sends the
report through your mail provider. The supplied Actions workflow uploads no
reports and caches only a duplicate-protection fingerprint. Full details and
cache limitations are in [AUTOMATION.md](AUTOMATION.md).

This is a small personal open-source utility under the [MIT license](LICENSE),
with no guaranteed support schedule. Hevy and provider APIs may change. The
[API notes](docs/API-REFERENCE.md) describe supported data shapes and assumptions.
Older [design notes](docs/archive/README.md) are historical ideas, not commitments.

```sh
python -m unittest discover -s tests -v
```

Tests use synthetic fixtures and mocked services; they need no keys and block
network connections. CI runs these tests and the demo. Please use synthetic data
in bug reports and never attach credentials or private workout exports.

## Troubleshooting

- **No workouts:** increase the fetch `--days` window, or omit `--days` when
  analyzing an older file. A change-feed export may contain incomplete history.
- **No load suggestion:** inspect the evidence for missing RPE, unknown targets,
  changed loads/set counts, or unmatched routine titles. This is intentionally cautious.
- **AI unavailable:** the base report still works. Check the key, credits, and
  model compatibility; details from remote errors are not printed to avoid leaks.
- **Email failed:** check the variable names above, credentials and STARTTLS port.
  The process exits nonzero and duplicate-protection state does not advance.
- **Upgrading an old checkout:** keep your .env and personal Python config files.
  They are no longer tracked; the old last_processed_state.json is not migrated.
  See [migration and automation notes](AUTOMATION.md#data-destinations-and-existing-files).
