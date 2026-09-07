"""Deterministic workout normalization and reports. No configuration or network I/O."""
from dataclasses import dataclass
import math
import re

import pandas as pd
from tabulate import tabulate


def timestamp(value):
    result = pd.to_datetime(value, utc=True, errors="raise")
    if pd.isna(result):
        raise ValueError("Workout is missing a timestamp")
    return result


def normalize_workouts(payload):
    """Accept a workout snapshot or legacy Hevy events (newest first).

    Keep the newest revision per ID; deletions win in event order. Legacy
    exports without IDs use a timestamp/title key, which cannot resolve ties.
    """
    if isinstance(payload, dict):
        payload = payload.get("workouts", payload.get("events"))
    if not isinstance(payload, list):
        raise ValueError("Expected a workouts list or an events list")
    revisions = []
    for index, item in enumerate(payload):
        event = item.get("type") in ("updated", "deleted")
        workout = item.get("workout", {}) if event else item
        identity = item.get("id") if item.get("type") == "deleted" else workout.get("id")
        identity = identity or item.get("workout_id")
        if not identity:
            identity = "legacy:" + str(workout.get("start_time")) + ":" + str(workout.get("title"))
        revised = item.get("updated_at") or item.get("deleted_at") or workout.get("updated_at")
        revisions.append((timestamp(revised).value if revised else None, -index, str(identity), item, workout))
    seen, workouts = set(), []
    # If any revision lacks a timestamp, use feed order throughout. Treating
    # missing time as zero could resurrect a workout after a newer deletion.
    have_times = all(r[0] is not None for r in revisions)
    ordered = sorted(revisions, key=lambda r: (r[0], r[1]) if have_times else (r[1],), reverse=True)
    for _, _, identity, item, workout in ordered:
        if identity in seen:
            continue
        seen.add(identity)
        if item.get("type") == "deleted":
            continue
        workout = dict(workout, id=identity)
        # Validate now, instead of silently discarding an unreadable session.
        timestamp(workout.get("start_time"))
        workouts.append(workout)
    return sorted(workouts, key=lambda w: (timestamp(w["start_time"]), w["id"]))


def filter_workouts(workouts, days, now=None):
    if days is None:
        return workouts
    end = timestamp(now) if now is not None else pd.Timestamp.now(tz="UTC")
    cutoff = end - pd.Timedelta(days=days)
    return [w for w in workouts if cutoff <= timestamp(w["start_time"]) <= end]


def is_assisted_exercise(name, overrides=None):
    if overrides and name in overrides:
        return overrides[name]
    return bool(re.search(r"\b(assisted|counterweight|counter weight)\b", name, re.I))


def number(value):
    if isinstance(value, bool) or value is None:
        return None
    try:
        result = float(value)
        return result if math.isfinite(result) and result >= 0 else None
    except (ValueError, TypeError):
        return None


def working_sets(exercise):
    return [s for s in exercise.get("sets", []) if s.get("type") in ("normal", "failure", "dropset")]


def volume(sets):
    """Logged load x reps, never average load x total reps. Unknown stays unknown."""
    pairs = [(number(s.get("weight_kg")), number(s.get("reps"))) for s in sets]
    if not pairs or any(w is None or r is None for w, r in pairs):
        return None
    return sum(w * r for w, r in pairs)


def fmt(value):
    return "unknown" if value is None else f"{value:g}"


def safe(value):
    """Keep user-provided labels from breaking Markdown layout or adding HTML."""
    import html
    text = html.escape(str(value)).replace("\n", " ").replace("\r", " ")
    return re.sub(r"([\\`*_{}\[\]()#+.!|>])", r"\\\1", text)


def performance(sets, assisted=False):
    if not sets:
        return "no working sets"
    values = [f"{fmt(number(s.get('weight_kg')))} kg × {fmt(number(s.get('reps')))}" for s in sets]
    suffix = " assistance" if assisted else ""
    return "; ".join(values) + suffix


def exercise_key(exercise):
    return exercise.get("exercise_template_id") or exercise.get("title", "Unknown exercise")


def context_key(workout):
    return workout.get("routine_id") or workout.get("title", "Untitled workout")


def previous_exercise(workouts, latest, exercise):
    matches = []
    for workout in workouts:
        if workout["id"] == latest["id"] or timestamp(workout["start_time"]) >= timestamp(latest["start_time"]):
            continue
        if context_key(workout) != context_key(latest):
            continue
        candidates = [e for e in workout.get("exercises", []) if exercise_key(e) == exercise_key(exercise)]
        if len(candidates) == 1:
            matches.append((workout, candidates[0]))
    return matches


def recommendation(current, previous, target, assisted, rpe_ceiling):
    """Conservative double progression; assumptions are exposed in the report."""
    if target is None:
        return "Set a rep target before considering a load change.", "No target is configured."
    if previous is None:
        return "Log another comparable session before changing load based on this report.", "Only one comparable session is available."
    if not current or len(current) != len(previous):
        return "Repeat a comparable set structure before deciding on load.", "Working-set counts differ or are empty."
    if any(s.get("type") != "normal" for s in current + previous):
        return "Compare normal sets before deciding on load.", "Failure or drop sets make this comparison less direct."
    reps = [number(s.get("reps")) for s in current + previous]
    weights = [number(s.get("weight_kg")) for s in current + previous]
    rpes = [number(s.get("rpe")) for s in current + previous]
    if any(r is None or r <= 0 for r in reps) or any(w is None for w in weights):
        return "Complete the rep and load logs before deciding on load.", "Reps or load are missing; timed/distance sets do not use rep targets."
    if any(r is None or not 6 <= r <= 10 for r in rpes):
        return "Record RPE on each working set and repeat before deciding on load.", "RPE is missing or invalid in the current or previous session."
    if len(set(weights)) != 1 or weights[0] == 0:
        return "Repeat a consistent logged load before deciding on a change.", "Loads vary, changed between sessions, or do not describe external resistance."
    lower, upper = target
    if all(r >= upper for r in reps) and max(rpes) <= rpe_ceiling:
        direction = "less assistance" if assisted else "more load"
        return f"Consider the smallest available step toward {direction}; then return to the lower end of the rep target.", f"Both sessions reached {upper:g}+ reps on every set at the same load with all RPE ≤ {rpe_ceiling:g}."
    if any(r < lower for r in reps[:len(current)]):
        direction = "more assistance" if assisted else "less load"
        return f"Repeat the load, or consider {direction} if the rep shortfall persists.", f"At least one current set is below the configured {lower:g}-rep floor; this alone does not establish why."
    return "Keep the logged load and work toward the top of the rep target.", "The two-session progression threshold has not been met."


@dataclass(frozen=True)
class Report:
    markdown: str
    ai_status: str


def generate_report(workouts, targets=None, assisted_overrides=None, rpe_ceiling=8.0,
                    demo=False, ai=None, cycle_hint=None):
    """Analyze once; optional commentary is called once, never by delivery code."""
    if not workouts:
        raise ValueError("No workouts in the selected history")
    targets = targets or {}
    latest = workouts[-1]
    changes, attention, recommendations, details = [], [], [], []
    latest_keys = [exercise_key(e) for e in latest.get("exercises", [])]
    for exercise in latest.get("exercises", []):
        name = exercise.get("title", "Unknown exercise")
        label = safe(name)
        assisted = is_assisted_exercise(name, assisted_overrides)
        current = working_sets(exercise)
        matches = previous_exercise(workouts, latest, exercise)
        if latest_keys.count(exercise_key(exercise)) != 1:
            matches = []  # Repeated exercise blocks are not safely comparable.
        prior_workout, prior_exercise = matches[-1] if matches else (None, None)
        previous = working_sets(prior_exercise) if prior_exercise else None
        current_volume = volume(current)
        previous_volume = volume(previous) if previous is not None else None
        current_text = performance(current, assisted)
        previous_text = performance(previous, assisted) if previous is not None else "unavailable"
        comparison = f"{previous_text} → {current_text}."
        if previous is None:
            comparison = f"{current_text}. No earlier comparable session in this history."
        elif not assisted and current_volume is not None and previous_volume is not None:
            comparison += f" Logged volume {current_volume - previous_volume:+g} kg·reps."
        elif assisted:
            comparison += " Lower assistance means greater resistance; assistance × reps is not lifted volume."
        changes.append(f"- **{label}:** {comparison}")
        rpes = [number(s.get("rpe")) for s in current]
        valid_rpes = [r for r in rpes if r is not None and 6 <= r <= 10]
        if len(valid_rpes) < len(current):
            attention.append(f"{label}: RPE recorded for {len(valid_rpes)}/{len(current)} working sets; effort is uncertain.")
        if valid_rpes and max(valid_rpes) >= 9:
            attention.append(f"{label}: logged RPE reaches {max(valid_rpes):g}; this describes reported effort, not recovery.")
        if not matches:
            attention.append(f"{label}: insufficient comparable history for a progression conclusion.")
        target = targets.get(name)
        if target is None:
            attention.append(f"{label}: no configured rep target.")
        action, reason = recommendation(current, previous, target, assisted, rpe_ceiling)
        target_text = f"{target[0]:g}–{target[1]:g} reps" if target else "not configured"
        prior_date = timestamp(prior_workout["start_time"]).strftime("%Y-%m-%d %H:%M UTC") if prior_workout else "unavailable"
        evidence = f"Previous ({prior_date}): {previous_text}. Current: {current_text}. Target: {target_text}. Reason: {reason}"
        recommendations.append((f"- **{label}:** {action}\n\n  {evidence}\n", action, evidence))
        details.append([label, len(current), sum(s.get("type") == "warmup" for s in exercise.get("sets", [])),
                        "not applicable" if assisted else fmt(current_volume),
                        f"{len(valid_rpes)}/{len(current)}", len(matches) + 1])
    if not changes:
        changes.append("- No exercises logged in the latest workout.")
    lines = ["# Hevy-Coach workout report", ""]
    if demo:
        lines += ["> SYNTHETIC DEMO — fictional workout history, fixed dates, no network access.", ""]
    lines += [f"**Latest:** {safe(latest.get('title', 'Untitled workout'))} · {timestamp(latest['start_time']).strftime('%Y-%m-%d %H:%M UTC')}", "",
              f"**History supplied:** {len(workouts)} workouts · {timestamp(workouts[0]['start_time']).strftime('%Y-%m-%d')} to {timestamp(latest['start_time']).strftime('%Y-%m-%d')}. This may be incomplete.", "",
              "## What changed", "", *changes, "", "## Observations worth attention", ""]
    lines += [f"- {item}" for item in attention[:3]] or ["- No additional data gaps flagged; this does not establish recovery or readiness."]
    if len(attention) > 3:
        lines.append("- Further data limits are included with the exercise evidence below.")
    lines += ["", "## Focus for the next comparable session", ""]
    lines += [r[0] for r in recommendations[:3]] or ["- Log working sets to enable comparisons."]
    if cycle_hint:
        lines += ["", f"**Configured cycle:** {safe(cycle_hint)}. This is your saved sequence, not a readiness prediction."]
    lines += ["", "## Details", "", tabulate(details, headers=["Exercise", "Work sets", "Warmups excluded", "kg·reps", "RPE logged", "Comparable sessions"], tablefmt="github"), ""]
    if len(recommendations) > 3:
        lines += ["### Remaining exercise evidence", "", *[r[0] for r in recommendations[3:]], ""]
    lines += ["### Recent session totals", ""]
    rows = []
    for workout in workouts[-6:]:
        sets = [s for e in workout.get("exercises", []) for s in working_sets(e)]
        weighted = [s for e in workout.get("exercises", []) if not is_assisted_exercise(e.get("title", ""), assisted_overrides) for s in working_sets(e)]
        rows.append([timestamp(workout["start_time"]).strftime("%Y-%m-%d %H:%M UTC"), safe(workout["id"]), len(sets), fmt(volume(weighted))])
    lines += [tabulate(rows, headers=["Started", "Workout ID", "Work sets", "kg·reps (excludes assisted)"], tablefmt="github"), "",
              "Comparisons use the same exercise template ID (name when absent) and routine ID (workout title when absent). Equipment, form, range of motion, and rest may still differ. Same-time sessions are not compared.", "",
              f"Load-change suggestions require two sessions at one positive logged load, equal normal-set counts, complete reps and RPE, every set at the rep ceiling, and every RPE ≤ {rpe_ceiling:g}. These are configurable heuristics, not validated coaching.", "",
              "Volume sums each working set's logged kg × reps. Unknown load/reps remain unknown; bodyweight is not estimated. Failure and drop sets appear in totals but block load progression suggestions. Warmups are excluded. CSV retains every set, including timed/distance work.", "",
              "This report does not infer recovery, injury risk, technique, or long-term progress from a few sessions."]
    # Send only supplied facts and deterministic suggestions, not raw notes or IDs.
    ai_status = "disabled"
    if ai is not None:
        try:
            commentary = ai({"changes": changes, "observations": attention,
                             "recommendations": [{"suggestion": r[1], "evidence": r[2]} for r in recommendations]})
            if not commentary or not commentary.strip():
                raise ValueError("Empty commentary")
            lines += ["", "## Optional AI commentary", "", safe(commentary.strip()), "", "AI wording may be inaccurate; use the evidence above to check it."]
            ai_status = "included"
        except Exception:
            lines += ["", "**AI commentary unavailable.** The deterministic report is complete."]
            ai_status = "unavailable"
    return Report("\n".join(lines) + "\n", ai_status)


def workouts_to_df(workouts):
    rows = []
    for workout in workouts:
        for ei, exercise in enumerate(workout.get("exercises", [])):
            for si, item in enumerate(exercise.get("sets", [])):
                rows.append({"workout_id": workout["id"], "start_time": workout["start_time"],
                             "workout": workout.get("title"), "exercise_template_id": exercise.get("exercise_template_id"),
                             "exercise": exercise.get("title"), "exercise_index": ei, "set_index": item.get("index", si),
                             "type": item.get("type"), "weight_kg": item.get("weight_kg"), "reps": item.get("reps"),
                             "rpe": item.get("rpe"), "duration_seconds": item.get("duration_seconds"),
                             "distance_meters": item.get("distance_meters"), "exercise_notes": exercise.get("notes")})
    return pd.DataFrame(rows)
