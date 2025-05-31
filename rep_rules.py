#!/usr/bin/env python3
# rep_rules.py
# --------------------------------------------
# Target rep ranges (min_reps, max_reps) used
# by the analysis script to judge whether a
# set is "in range", "too heavy" (below range),
# or "too light" (above range).
#
# Note: Warm-ups, cardio, and other non-strength
# exercises are automatically excluded from analysis.
# See EXCLUDED_EXERCISES in hevy_stats.py

REP_RANGE = {
    # ──────────── LEGS ────────────
    "Leg Press Horizontal (Machine)":     (10, 12),
    "Leg Press (Machine)":                (10, 12),
    "Bulgarian Split Squat":              (8, 12),
    "Walking Lunge":                      (12, 15),

    "Leg Extension (Machine)":            (12, 15),
    "Leg Curl (Machine)":                 (12, 15),
    "Standing Leg Curls":                 (10, 12),

    "Calf Raise (Machine)":               (15, 20),
    "Calf Press (Machine)":               (12, 15),
    "Standing Calf Raise":                (12, 15),

    "Hip Abduction (Machine)":            (12, 15),

    # ──────────── BACK / PULL ────────────
    "Lat Pulldown (Machine)":             (10, 12),
    "Pulldown (Cable)":                   (10, 12),
    "Seated Cable Row - V Grip (Cable)":  (10, 12),
    "Seated Row (Machine)":               (10, 12),
    "Cable Row (Cable)":                  (10, 12),

    "Barbell Row":                        (8, 10),
    "T-Bar Row":                          (8, 12),
    "Pull Up":                            (6, 10),
    "Shrug (Dumbbell)":                   (10, 15),

    # ──────────── CHEST / PUSH ───────────
    "Bench Press (Barbell)":              (6, 10),
    "Bench Press (Dumbbell)":             (8, 12),
    "Incline Bench Press (Barbell)":      (8, 10),
    "Incline Bench Press (Dumbbell)":     (8, 12),

    "Chest Press (Machine)":              (10, 12),
    "Chest Press - MTS":                  (8, 12),
    "Incline Chest Press (Machine)":      (8, 12),
    "Chest Dip (Assisted)":               (8, 12),
    "Seated Dip Machine":                 (8, 12),
    "Push Up":                            (12, 20),

    # ──────────── SHOULDERS ──────────────
    "Shoulder Press (Dumbbell)":          (8, 12),
    "Shoulder Press (Machine)":           (10, 12),
    "Seated Shoulder Press (Machine)":    (8, 12),

    "Lateral Raise (Dumbbell)":           (12, 15),
    "Lateral Raise (Machine)":            (15, 20),

    "Rear Delt Reverse Fly (Machine)":    (12, 15),
    "Face Pull (Cable)":                  (15, 20),
    "Face Pull":                          (15, 20),   # alias
    "Upright Row":                        (10, 12),

    # ──────────── ARMS ───────────────────
    "Bicep Curl (Dumbbell)":              (10, 12),
    "Bicep Curl (Barbell)":               (8, 12),
    "Bicep Curl (Machine)":               (10, 12),

    "Hammer Curl (Dumbbell)":             (10, 12),
    "Hammer Curl (Cable)":                (10, 12),

    "Tricep Extension (Dumbbell)":        (10, 12),
    "Tricep Pushdown (Cable)":            (12, 15),
    "Triceps Rope Pushdown":              (10, 12),
    "Close Grip Bench Press":             (8, 10),

    # ──────────── CORE / CONDITIONING ────
    "Plank":                              (30, 60),   # seconds
    "Crunch":                             (15, 25),
    "Russian Twist":                      (20, 30),   # reps per side
    "Dead Bug":                           (10, 15),
    "Hanging Knee Raise":                 (12, 15),
    "Mountain Climber":                   (20, 30),   # reps per side

    # ──────────── COMPOUND BARBELL LIFTS ─
    "Squat (Barbell)":                    (6, 10),
    "Deadlift (Barbell)":                 (5, 8),
    "Romanian Deadlift":                  (8, 12),
    "Romanian Deadlift (Dumbbell)":       (8, 12),
    "Overhead Press (Barbell)":           (6, 10),

    # ──────────── OTHER STRENGTH EXERCISES ─
    "Squat (Bodyweight)":                 (15, 25),
    "Chest Fly (Machine)":                (12, 15),
}
