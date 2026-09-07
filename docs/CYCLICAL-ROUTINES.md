# Optional routine hint

Copy routine_config.example.py to routine_config.local.py only if you want a
saved-sequence hint. Edit `CYCLE_PATTERN` and `ROUTINE_TITLE_MAPPING` so titles
match your Hevy workouts exactly. Existing routine_config.py remains supported
as a fallback; neither file is tracked by Git.

When the latest workout title matches a configured index, the report displays
the next entry in that sequence, including a rest entry if configured. An unknown
title produces no hint. This is not a forecast of readiness or a training plan.
The old keyword guesses in `EXERCISE_PATTERNS` are no longer used. The CLI does
not contact the Hevy routines endpoint.
