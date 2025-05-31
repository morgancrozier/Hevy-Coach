# Copy this file to rep_rules.py and customize your target rep ranges
# Format: "Exercise Name": (min_reps, max_reps)
# Set to None if you don't want rep range analysis for an exercise

REP_RANGE = {
    # Compound Movements (Lower Reps)
    "Squat": (6, 8),
    "Deadlift": (5, 8),
    "Bench Press": (6, 10),
    "Overhead Press": (6, 10),
    
    # Machine/Isolation (Higher Reps)
    "Leg Press": (10, 12),
    "Leg Extension": (12, 15),
    "Leg Curl": (12, 15),
    "Chest Press": (8, 12),
    "Lat Pulldown": (8, 12),
    "Cable Row": (8, 12),
    
    # Accessories (Higher Reps)
    "Bicep Curl": (12, 15),
    "Tricep Extension": (12, 15),
    "Lateral Raise": (12, 15),
    "Face Pull": (15, 20),
    "Calf Raise": (15, 20),
    
    # Add your exercises here following the same pattern
    # "Your Exercise Name": (min_reps, max_reps),
} 