# Optional automation

The report workflow is manual-only. Nothing in local setup enables a schedule,
sends email, or changes GitHub settings. The separate offline-test workflow runs
on pushes and pull requests without secrets.

## GitHub Actions

After reviewing the data handling below, configure the `HEVY_API_KEY` repository
secret. Optional secrets are `OPENAI_API_KEY`, `EMAIL_USER`, `EMAIL_PASSWORD`,
`TO_EMAIL`, `SMTP_SERVER`, and `SMTP_PORT`; defaults match env.example. Set the
optional `OPENAI_MODEL` repository variable to override `gpt-4o-mini`.

Run **Hevy report (manual)** from the Actions tab. Email and AI are separate,
default-off inputs. With both disabled, the workflow generates and discards the
report, useful as a setup check. With email enabled, an SMTP failure fails the job.
To see a report without email, run locally; the public workflow does not upload
reports. Review private targets before automating: local ignored configuration
files are absent on runners, so targets are unknown unless you deliberately add
non-personal configuration to your own workflow.

The job installs requirements.txt, fetches a 30-day snapshot, and runs with
`--quiet`. It persists only an opaque SHA-256 fingerprint through Actions cache,
after requested outputs succeed. Repository contents permission is read-only.
No source-branch state commits are needed. Concurrency serializes runs for each
branch, and canceled or failed runs do not save new cache state.

Cache persistence is **best effort**. GitHub may evict caches, including those
unused for seven days; branch scope also affects restoration. A lost cache means
the next run may send a duplicate. A crash after SMTP accepts a message but before
state/cache save can also cause a resend. SMTP acceptance is not proof of inbox
delivery. There is no exactly-once guarantee. See [GitHub cache limits and access
rules](https://docs.github.com/en/actions/reference/workflows-and-actions/dependency-caching).

The fingerprint covers the latest workout contents, email destination/delivery
choice, and whether AI was requested. It does not track a queue of every new
workout: several workouts between checks produce one report about the latest.
Changes to older workouts, targets, model, or other settings require the **force**
input to regenerate an unchanged latest workout. AI failure counts as successful
report generation when the deterministic fallback and all requested deliveries
succeed; force a rerun if commentary is needed.

## Local use

After the README setup, an explicit local email run with duplicate protection is:

```sh
python hevy_stats.py both --email --state-file .hevy-state/processed.json
```

Omit `--email` for terminal output; add `--save-markdown` and/or `--save-csv` to
keep files. Use `--force` with `--state-file` to bypass a match. Run only one local
process per state file; atomic file replacement protects against partial writes,
but is not a multi-process lock. Malformed state fails visibly; inspect or move it
aside yourself instead of silently treating it as a first run.

If you later choose cron, use absolute paths for both the working directory and
virtualenv Python, quote paths containing spaces, and choose the timezone and
frequency yourself. Hevy asks clients to avoid requests exactly on the hour.
The previous workflow used 09:00–11:30 UTC at half-hour intervals (16:00–18:30 in
Thailand). This historical personal window is recorded here, not enabled as a
public default. The setup shell helper now only points to this guide.

## Data destinations and existing files

- Local fetching writes the raw snapshot to hevy_events.json (or `--outfile`),
  including any notes present in the API response. Reports/CSV are written only
  when requested. Their default directory is reports/.
- `--ai` sends exercise labels, set-performance comparisons, rep targets,
  recommendations, and relevant session dates to OpenAI. Raw notes, credentials,
  workout IDs and full raw history are not included in the prompt. Provider data
  handling applies; see [OpenAI API data controls](https://platform.openai.com/docs/guides/your-data).
- `--email` submits the report and a Markdown attachment through your SMTP
  provider to `TO_EMAIL` (or the sender). Your providers control retention.
- The Actions runner temporarily holds fetched history and report content.
  The supplied workflow hides report text and uploads no report/raw-data
  artifacts. Cache contains only the fingerprint. Removing `--quiet`, adding
  exports/artifact uploads, or printing raw data can expose workout data in
  GitHub logs/artifacts; public repository logs are public.

Personal rep_rules.py, routine_config.py, and last_processed_state.json are now
ignored and no longer part of the tracked tree; existing local copies remain.
The CLI still supports the first two. It does not read or migrate the old state
file automatically: the first run with the new state path may repeat a report.
Previously committed files remain in Git history, and prior Actions artifacts
or logs may still exist. This cleanup does not rewrite history or remove those
remote records.
