# Data and API notes

The CLI uses Hevy's paginated `GET /v1/workouts` endpoint, with `pageSize=10`
and a 30-second request timeout. It fetches every page before filtering by
`start_time` in UTC, because the API does not document an ordering guarantee.
Large histories therefore need more requests even with a short `--days` window.
No Hevy write endpoints or routine requests are made.

The saved JSON is a snapshot: `{"workouts": [...]}`. Existing lists of Hevy
`updated`/`deleted` events and `{"events": [...]}` files can also be analyzed.
Revisions are deduplicated by workout ID using revision timestamps when
available, otherwise the documented newest-first event order. Deleted workouts
are excluded. An old event export is still only the changes it captured; it
cannot reconstruct omitted history. Fetch a fresh snapshot when possible.

Exercise matching uses template ID, falling back to exact name. Comparable
sessions also need the same routine ID, falling back to exact workout title.
Distinct workout IDs remain distinct even on the same day. Older exports without
IDs use timestamp + title and cannot distinguish an exact tie. Timestamps without
an offset are treated as UTC. Same-time sessions are not compared.

Null values are retained. Warmups are excluded from report totals; normal,
failure, and drop sets are included. Only normal sets qualify for progression
suggestions. Unknown set types are retained in CSV but excluded from analysis.
Duration/distance data remain in CSV; there is no pace or endurance coaching.

AI uses the existing Chat Completions API with `gpt-4o-mini` by default and
`OPENAI_MODEL` as its only model override. One short request receives the generated
observations and recommendations. Retries are disabled; a failure retains the
base report. Other models must support Chat Completions, `max_tokens`, and
`temperature`; compatibility is not automatically negotiated.

Checked against the official [Hevy API schema](https://api.hevyapp.com/docs/)
and [OpenAI Chat Completions reference](https://developers.openai.com/api/reference/resources/chat)
on 2026-09-07. This was documentation and mock verification, not a live integration test.
