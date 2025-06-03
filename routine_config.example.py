# 🔄 Routine Configuration Example
# Copy this file to `routine_config.py` and customize for your workout routine

# =============================================================================
# WORKOUT CYCLE PATTERN
# =============================================================================

# Example 1: 6-Day Push/Pull/Legs with Rest Days
CYCLE_PATTERN = [
    "Day 1 - Upper (Push) 💪",
    "Day 2 - Lower (Hamstring) 🦵",
    "Day 3 - Rest / Treadmill",
    "Day 4 - Upper (Pull) 💪",
    "Day 5 - Lower (Quad) 🦵",
    "Day 6 - Rest"
]

ROUTINE_TITLE_MAPPING = {
    "Day 1 - Upper (Push) 💪": 0,
    "Day 2 - Lower (Hamstring) 🦵": 1,
    "Day 3 - Upper (Pull) 💪": 3,
    "Day 4 - Lower (Quad) 🦵": 4
}

# =============================================================================
# EXERCISE PATTERN HEURISTICS (for when title matching fails)
# =============================================================================

EXERCISE_PATTERNS = {
    "upper_push": {
        "keywords": ["chest", "press", "shoulder", "dip", "tricep", "push"],
        "next_cycle_day": 1
    },
    "lower_hamstring": {
        "keywords": ["curl", "deadlift", "hamstring", "hip", "glute", "rdl"],
        "next_cycle_day": 2
    },
    "upper_pull": {
        "keywords": ["lat", "pull", "row", "bicep", "chin", "pulldown"],
        "next_cycle_day": 4
    },
    "lower_quad": {
        "keywords": ["quad", "extension", "squat", "leg press", "lunge"],
        "next_cycle_day": 5
    }
}

# =============================================================================
# ALTERNATIVE ROUTINE EXAMPLES
# =============================================================================

# Uncomment ONE of these sections to use a different routine:

# # Example 2: 4-Day Upper/Lower Split
# CYCLE_PATTERN = [
#     "Upper Body A",
#     "Lower Body A",
#     "Rest",
#     "Upper Body B", 
#     "Lower Body B",
#     "Rest",
#     "Rest"
# ]
# 
# ROUTINE_TITLE_MAPPING = {
#     "Upper Body A": 0,
#     "Lower Body A": 1,
#     "Upper Body B": 3,
#     "Lower Body B": 4
# }
# 
# EXERCISE_PATTERNS = {
#     "upper": {
#         "keywords": ["bench", "press", "row", "pull", "shoulder", "arm"],
#         "next_cycle_day": 1  # Upper → Lower
#     },
#     "lower": {
#         "keywords": ["squat", "deadlift", "leg", "glute", "quad", "hamstring"],
#         "next_cycle_day": 2  # Lower → Rest
#     }
# }

# # Example 3: 3-Day Full Body
# CYCLE_PATTERN = [
#     "Full Body A",
#     "Rest",
#     "Full Body B",
#     "Rest", 
#     "Full Body C",
#     "Rest",
#     "Rest"
# ]
# 
# ROUTINE_TITLE_MAPPING = {
#     "Full Body A": 0,
#     "Full Body B": 2,
#     "Full Body C": 4
# }

# # Example 4: 5-Day Bro Split
# CYCLE_PATTERN = [
#     "Chest Day",
#     "Back Day",
#     "Shoulder Day",
#     "Arm Day",
#     "Leg Day",
#     "Rest",
#     "Rest"
# ]
# 
# ROUTINE_TITLE_MAPPING = {
#     "Chest Day": 0,
#     "Back Day": 1,
#     "Shoulder Day": 2,
#     "Arm Day": 3,
#     "Leg Day": 4
# }

# =============================================================================
# SETUP INSTRUCTIONS
# =============================================================================
"""
🚀 Quick Setup:

1. Copy this file: `cp routine_config.example.py routine_config.py`
2. Edit `routine_config.py` with your actual routine
3. Make sure routine titles match your Hevy app exactly
4. Test: `python hevy_stats.py analyze`

📝 Tips:
- Use the exact same titles as your saved routines in Hevy
- Include emojis and spacing exactly as they appear in Hevy
- Rest days don't need to be in ROUTINE_TITLE_MAPPING
- EXERCISE_PATTERNS are fallback when title matching fails

🔧 Troubleshooting:
- "No routine data available" → Check titles match exactly
- Wrong next workout predicted → Verify recent workout titles
- System falls back to exercise analysis → Add missing titles to mapping
""" 