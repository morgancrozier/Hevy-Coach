"""Offline regression tests: no API keys or services are needed."""
import contextlib
from copy import deepcopy
import io
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import Mock, patch

import hevy_stats as cli
from reporting import (filter_workouts, generate_report, is_assisted_exercise,
                       normalize_workouts, recommendation, volume, workouts_to_df)

FIXTURE = json.loads((cli.ROOT / "examples/demo_workouts.json").read_text())


def workout(identity="one", time="2025-01-01T09:00:00Z", weights=(20, 40), reps=(10, 5), rpe=(8, 8), name="Row"):
    return {"id": identity, "title": "Upper", "start_time": time, "exercises": [{
        "title": name, "exercise_template_id": name,
        "sets": [{"type": "normal", "weight_kg": w, "reps": r, "rpe": p}
                 for w, r, p in zip(weights, reps, rpe)]}]}


class OfflineTest(unittest.TestCase):
    def setUp(self):
        # A missed mock must fail loudly instead of contacting a live service.
        for target in ("socket.socket.connect", "socket.create_connection"):
            block = patch(target, side_effect=AssertionError("Network forbidden in offline tests"))
            block.start()
            self.addCleanup(block.stop)


class AnalysisTests(OfflineTest):
    def test_mixed_weight_volume(self):
        w = workout()
        self.assertEqual(volume(w["exercises"][0]["sets"]), 400)
        report = generate_report(normalize_workouts([w])).markdown
        self.assertIn("400", report)
        w["exercises"][0]["sets"][0]["weight_kg"] = None
        self.assertIsNone(volume(w["exercises"][0]["sets"]))

    def test_two_workouts_same_date_keep_identity_and_time(self):
        morning = workout()
        evening = workout("two", "2025-01-01T17:00:00Z", reps=(11, 6))
        history = normalize_workouts([evening, morning])
        report = generate_report(history, {"Row": (5, 12)}).markdown
        self.assertIn("Previous (2025-01-01 09:00 UTC)", report)
        self.assertIn("Logged volume +60", report)
        self.assertEqual(workouts_to_df(history)["workout_id"].nunique(), 2)
        self.assertEqual(len(workouts_to_df(history)), 4)

    def test_missing_rpe_and_insufficient_history(self):
        first = workout(weights=(20, 20), reps=(12, 12), rpe=(None, 8))
        second = deepcopy(first)
        second.update(id="two", start_time="2025-01-02T09:00:00Z")
        report = generate_report(normalize_workouts([first, second]), {"Row": (8, 12)}).markdown
        self.assertIn("Record RPE on each working set", report)
        self.assertNotIn("Consider the smallest", report)
        self.assertNotIn("nan", report.lower())
        self.assertIn("Only one comparable session", generate_report([first], {"Row": (8, 12)}).markdown)
        self.assertIn("No target is configured", generate_report([first]).markdown)

    def test_assistance_direction_and_exact_override(self):
        self.assertFalse(is_assisted_exercise("Chest Supported Row"))
        self.assertFalse(is_assisted_exercise("Support Grip Press"))
        self.assertTrue(is_assisted_exercise("Pull Up (Assisted)"))
        self.assertTrue(is_assisted_exercise("Machine Pull", {"Machine Pull": True}))
        self.assertFalse(is_assisted_exercise("Assisted label", {"Assisted label": False}))
        sets = workout(weights=(30, 30), reps=(12, 12))["exercises"][0]["sets"]
        self.assertIn("less assistance", recommendation(sets, sets, (8, 12), True, 8)[0])
        self.assertIn("more load", recommendation(sets, sets, (8, 12), False, 8)[0])
        low = deepcopy(sets)
        low[0]["reps"] = 7
        self.assertIn("more assistance", recommendation(low, sets, (8, 12), True, 8)[0])
        report = generate_report([workout(name="Pull Up (Assisted)")]).markdown
        self.assertIn("not applicable", report)

    def test_incomplete_or_changed_sets_block_progression(self):
        sets = workout(weights=(20, 20), reps=(12, 12))["exercises"][0]["sets"]
        for key, value in (("reps", None), ("weight_kg", None), ("rpe", 11), ("type", "failure")):
            current = deepcopy(sets)
            current[0][key] = value
            self.assertNotIn("Consider the smallest", recommendation(current, sets, (8, 12), False, 8)[0])
        self.assertNotIn("Consider the smallest", recommendation(sets[:1], sets, (8, 12), False, 8)[0])

    def test_no_cross_routine_or_template_comparison(self):
        first = workout()
        second = workout("two", "2025-01-02T09:00:00Z")
        second["title"] = "Different routine"
        self.assertIn("No earlier comparable session", generate_report([first, second]).markdown)
        second["title"] = first["title"]
        second["exercises"][0]["exercise_template_id"] = "different-machine"
        self.assertIn("No earlier comparable session", generate_report([first, second]).markdown)

    def test_events_deduplicated_and_deletions_honored(self):
        older = workout()
        older["updated_at"] = "2025-01-01T10:00:00Z"
        newer = deepcopy(older)
        newer["updated_at"] = "2025-01-02T10:00:00Z"
        newer["exercises"][0]["sets"][0]["reps"] = 12
        events = [{"type": "updated", "workout": older}, {"type": "updated", "workout": newer}]
        self.assertEqual(normalize_workouts(events)[0]["exercises"][0]["sets"][0]["reps"], 12)
        events.insert(0, {"type": "deleted", "id": "one", "deleted_at": "2025-01-03T10:00:00Z"})
        self.assertEqual(normalize_workouts(events), [])
        no_dates = [{"type": "deleted", "id": "one"}, {"type": "updated", "workout": workout()}]
        self.assertEqual(normalize_workouts(no_dates), [])
        no_dates[1]["workout"]["updated_at"] = "2025-01-01T10:00:00Z"
        self.assertEqual(normalize_workouts(no_dates), [])

    def test_nulls_set_types_and_timed_work_survive_export(self):
        w = workout()
        w["exercises"][0]["sets"] += [{"type": "warmup", "weight_kg": 10, "reps": 5},
                                     {"type": "dropset", "weight_kg": 10, "reps": 8},
                                     {"type": "normal", "duration_seconds": 60, "reps": None}]
        frame = workouts_to_df([w])
        self.assertEqual(len(frame), 5)
        self.assertEqual(frame.iloc[-1]["duration_seconds"], 60)
        self.assertTrue(frame["reps"].isna().iloc[-1])

    def test_fixed_fixture_does_not_age_out(self):
        history = normalize_workouts(FIXTURE["workouts"])
        self.assertEqual(len(filter_workouts(history, None, now="2099-01-01")), 5)
        self.assertEqual(filter_workouts(history, 30, now="2099-01-01"), [])
        expected = (cli.ROOT / "examples/demo-report.md").read_text()
        self.assertEqual(generate_report(history, FIXTURE["targets"], demo=True).markdown, expected)

    def test_ai_once_and_failure_fallback(self):
        ai = Mock(return_value="A short explanation.")
        report = generate_report(normalize_workouts(FIXTURE["workouts"]), FIXTURE["targets"], ai=ai)
        self.assertEqual(ai.call_count, 1)
        self.assertIn("A short explanation", report.markdown)
        ai.assert_called_once()
        ai.side_effect = RuntimeError("private response body")
        report = generate_report([workout()], ai=ai)
        self.assertEqual(report.ai_status, "unavailable")
        self.assertIn("What changed", report.markdown)
        self.assertNotIn("private response body", report.markdown)


class CLITests(OfflineTest):
    def setUp(self):
        super().setUp()
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.input = self.root / "input.json"
        self.input.write_text(json.dumps(FIXTURE))
        self.stdout = io.StringIO()
        for target, value in (("dotenv.load_dotenv", False), ("hevy_stats.load_analysis_settings", (FIXTURE["targets"], {}, 8)),
                              ("hevy_stats.cycle_hint", None)):
            mock = patch(target, return_value=value)
            mock.start()
            self.addCleanup(mock.stop)
        env = patch.dict(os.environ, {"OPENAI_API_KEY": "synthetic-unused"}, clear=True)
        env.start()
        self.addCleanup(env.stop)

    def run_cli(self, *args):
        with contextlib.redirect_stdout(self.stdout), contextlib.redirect_stderr(io.StringIO()):
            return cli.main(list(args))

    def test_terminal_markdown_email_share_one_report(self):
        with patch("hevy_stats.ai_commentary", return_value="Supplied facts explained.") as ai, patch.object(cli.EmailSender, "send_report", return_value=True) as email:
            self.assertEqual(self.run_cli("analyze", "--infile", str(self.input), "--ai", "--email", "--save-markdown", "--output-dir", str(self.root)), 0)
        ai.assert_called_once()
        saved = next(self.root.glob("hevy_coaching_report_*.md")).read_text()
        self.assertEqual(email.call_args.args[0], saved)
        self.assertTrue(self.stdout.getvalue().startswith(saved))

    def test_state_only_after_success_and_duplicate_skip(self):
        state = self.root / "state.json"
        args = ["analyze", "--infile", str(self.input), "--state-file", str(state), "--email", "--ai"]
        with patch.object(cli.EmailSender, "send_report", return_value=False), patch("hevy_stats.ai_commentary", return_value="Facts"):
            self.assertEqual(self.run_cli(*args), 1)
        self.assertFalse(state.exists())
        with patch.object(cli.EmailSender, "send_report", return_value=True) as email, patch("hevy_stats.ai_commentary", return_value="Facts") as ai:
            self.assertEqual(self.run_cli(*args), 0)
            self.assertEqual(self.run_cli(*args), 0)
            email.assert_called_once()
            ai.assert_called_once()
        state_before = state.read_bytes()
        with patch.object(cli.EmailSender, "send_report", return_value=False), patch("hevy_stats.ai_commentary", return_value="Facts"):
            self.assertEqual(self.run_cli(*args, "--force"), 1)
        self.assertEqual(state.read_bytes(), state_before)
        self.assertEqual(set(json.loads(state.read_text())), {"fingerprint"})

    def test_failed_file_output_does_not_advance_state_or_send(self):
        state = self.root / "state.json"
        with patch.object(cli.EmailSender, "send_report") as email:
            self.assertEqual(self.run_cli("analyze", "--infile", str(self.input), "--email", "--save-markdown", "--output-dir", str(self.input), "--state-file", str(state)), 1)
            email.assert_not_called()
        self.assertFalse(state.exists())

    def test_both_analyzes_fresh_outfile_not_stale_infile(self):
        fetched = [workout("fresh")]
        with patch.object(cli.HevyStatsClient, "get_all_recent_workouts", return_value=fetched), patch.dict(os.environ, {"HEVY_API_KEY": "unused"}):
            result = self.run_cli("both", "--outfile", str(self.root / "fresh.json"), "--infile", str(self.root / "nonexistent.json"))
        self.assertEqual(result, 0)
        self.assertIn("fresh", self.stdout.getvalue())

    def test_snapshot_endpoint_paginates_without_mutating_nulls(self):
        responses = []
        for w in (workout(), workout("two", "2025-01-02T09:00:00Z", rpe=(None, 8))):
            r = Mock()
            r.json.return_value = {"page_count": 2, "workouts": [w]}
            responses.append(r)
        with patch("hevy_stats.requests.get", side_effect=responses) as get:
            history = cli.HevyStatsClient("unused").get_all_recent_workouts(days=None)
        self.assertEqual(len(history), 2)
        self.assertIsNone(history[-1]["exercises"][0]["sets"][0]["rpe"])
        self.assertEqual(get.call_count, 2)
        self.assertTrue(all(c.args[0].endswith("/v1/workouts") for c in get.call_args_list))
        self.assertEqual(get.call_args.kwargs["params"]["page"], 2)
        self.assertEqual(get.call_args.kwargs["timeout"], 30)

    def test_smtp_refusal_and_exception_report_failure(self):
        with patch.dict(os.environ, {"EMAIL_USER": "synthetic@example.invalid", "EMAIL_PASSWORD": "unused"}):
            sender = cli.EmailSender()
        server = Mock()
        server.__enter__ = Mock(return_value=server)
        server.__exit__ = Mock(return_value=False)
        for outcome in ({"refused@example.invalid": (550, b"refused")}, RuntimeError("private body")):
            with patch.object(sender, "_connect", return_value=server), contextlib.redirect_stderr(io.StringIO()) as err:
                server.send_message.side_effect = outcome if isinstance(outcome, Exception) else None
                server.send_message.return_value = outcome
                self.assertFalse(sender.send_report("Synthetic report"))
                self.assertNotIn("private body", err.getvalue())

    def test_ai_model_is_configurable_without_api_call(self):
        with patch("openai.OpenAI") as constructor, patch.dict(os.environ, {"OPENAI_MODEL": "compatible-test-model"}):
            constructor.return_value.chat.completions.create.return_value.choices = [Mock(message=Mock(content="Facts"))]
            self.assertEqual(cli.AICoach().explain({"observations": []}), "Facts")
            self.assertEqual(constructor.return_value.chat.completions.create.call_args.kwargs["model"], "compatible-test-model")
            self.assertEqual(constructor.call_args.kwargs["max_retries"], 0)

    def test_import_and_demo_isolated_even_with_all_delivery_flags(self):
        # Run a new interpreter from a directory full of traps. Real user files
        # are never inspected; ROOT is redirected to a synthetic-only directory.
        examples = self.root / "examples"
        examples.mkdir()
        (examples / "demo_workouts.json").write_text(json.dumps(FIXTURE))
        for name in (".env", "rep_rules.py", "routine_config.py", "hevy_events.json", "last_processed_state.json"):
            (self.root / name).write_text("PERSONAL SENTINEL DO NOT READ OR CHANGE")
        script = '''
import builtins, os, pathlib, socket, sys
sys.path.insert(0, sys.argv[1])
socket.socket.connect = lambda *a, **k: (_ for _ in ()).throw(AssertionError("network"))
import hevy_stats
hevy_stats.ROOT = pathlib.Path.cwd()
original = builtins.open
original_path_open = pathlib.Path.open
blocked = {".env", "rep_rules.py", "routine_config.py", "hevy_events.json", "last_processed_state.json"}
def guarded(file, *args, **kwargs):
    assert pathlib.Path(file).name not in blocked, "personal read"
    return original(file, *args, **kwargs)
def guarded_path(self, *args, **kwargs):
    assert self.name not in blocked, "personal read"
    return original_path_open(self, *args, **kwargs)
builtins.open = guarded
pathlib.Path.open = guarded_path
raise SystemExit(hevy_stats.main(["--demo", "--email", "--ai", "--test-email", "--save-csv", "--save-markdown", "--state-file", "last_processed_state.json", "--outfile", "hevy_events.json"]))
'''
        before = {str(p.relative_to(self.root)): p.read_bytes() for p in self.root.rglob("*") if p.is_file()}
        result = subprocess.run([sys.executable, "-B", "-c", script, str(cli.ROOT)], cwd=self.root,
                                env={**os.environ, "HEVY_API_KEY": "unused", "EMAIL_USER": "unused", "EMAIL_PASSWORD": "unused"}, capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("SYNTHETIC DEMO", result.stdout)
        after = {str(p.relative_to(self.root)): p.read_bytes() for p in self.root.rglob("*") if p.is_file()}
        self.assertEqual(before, after)


if __name__ == "__main__":
    unittest.main()
