# 🔄 Routine Configuration
# Configure your workout cycle pattern and routine mappings here

# =============================================================================
# WORKOUT CYCLE PATTERN
# =============================================================================
# Define your workout cycle as a list of workout names.
# The system will cycle through these in order.
# Rest days can be included and will be handled appropriately.

CYCLE_PATTERN = [
    "Day 1 - Upper (Push) 💪",     # Chest, shoulders, triceps
    "Day 2 - Lower (Hamstring) 🦵", # Deadlifts, leg curls, hip movements
    "Day 3 - Rest / Treadmill",     # Recovery or light cardio
    "Day 4 - Upper (Pull) 💪",     # Back, biceps, rear delts
    "Day 5 - Lower (Quad) 🦵",     # Squats, leg press, leg extensions
    "Day 6 - Rest"                 # Complete rest
]

# =============================================================================
# ROUTINE TITLE MAPPING
# =============================================================================
# Map your Hevy routine titles to cycle day indices.
# The keys should match the exact titles of your saved routines in Hevy.
# The values should be the index position in CYCLE_PATTERN (starting from 0).
# Rest days typically don't need saved routines, so they're excluded.

ROUTINE_TITLE_MAPPING = {
    "Day 1 - Upper (Push) 💪": 0,      # Maps to CYCLE_PATTERN[0]
    "Day 2 - Lower (Hamstring) 🦵": 1,  # Maps to CYCLE_PATTERN[1]
    "Day 3 - Upper (Pull) 💪": 3,      # Maps to CYCLE_PATTERN[3] (Day 4 in cycle)
    "Day 4 - Lower (Quad) 🦵": 4       # Maps to CYCLE_PATTERN[4] (Day 5 in cycle)
    # Note: Rest days (indices 2 and 5) don't need routine mappings
}

# =============================================================================
# EXERCISE PATTERN HEURISTICS
# =============================================================================
# When routine title matching fails, the system analyzes exercise names
# to guess the workout type. Define keywords for each muscle group/movement pattern.

EXERCISE_PATTERNS = {
    "upper_push": {
        "keywords": ["chest", "press", "shoulder", "dip", "tricep", "push"],
        "next_cycle_day": 1  # After upper push → lower hamstring
    },
    "lower_hamstring": {
        "keywords": ["curl", "deadlift", "hamstring", "hip", "glute", "rdl", "sldl"],
        "next_cycle_day": 2  # After lower hamstring → rest/treadmill
    },
    "upper_pull": {
        "keywords": ["lat", "pull", "row", "bicep", "chin", "pulldown"],
        "next_cycle_day": 4  # After upper pull → lower quad
    },
    "lower_quad": {
        "keywords": ["quad", "extension", "squat", "leg press", "lunge", "front squat"],
        "next_cycle_day": 5  # After lower quad → rest
    }
}

# =============================================================================
# EXAMPLE ALTERNATIVE CYCLES
# =============================================================================
# Uncomment and modify one of these to use a different routine structure:

# # 4-Day Upper/Lower Split
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

# # 3-Day Push/Pull/Legs
# CYCLE_PATTERN = [
#     "Push Day",
#     "Pull Day", 
#     "Leg Day",
#     "Rest",
#     "Rest"
# ]
# 
# ROUTINE_TITLE_MAPPING = {
#     "Push Day": 0,
#     "Pull Day": 1,
#     "Leg Day": 2
# }

# # 5-Day Bro Split
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
# CONFIGURATION NOTES
# =============================================================================
"""
📝 Configuration Tips:

1. **Routine Titles**: Make sure the keys in ROUTINE_TITLE_MAPPING exactly 
   match the titles of your saved routines in the Hevy app.

2. **Cycle Length**: You can have any cycle length - 3, 4, 5, 6, 7 days, etc.
   The system will automatically cycle through your pattern.

3. **Rest Days**: Include rest days in your CYCLE_PATTERN but don't add them
   to ROUTINE_TITLE_MAPPING since they don't need saved routines.

4. **Exercise Keywords**: If title matching fails, the system uses exercise
   name analysis. Make sure EXERCISE_PATTERNS includes keywords from your
   actual exercise names.

5. **Multiple Routines**: If you have different versions of the same day
   (e.g., "Upper A" and "Upper B"), you can map them to the same cycle index.

🚀 Getting Started:
1. Look at your saved routines in Hevy
2. Modify CYCLE_PATTERN to match your workout schedule  
3. Update ROUTINE_TITLE_MAPPING with your exact routine titles
4. Test with: python hevy_stats.py analyze

🔧 Troubleshooting:
- Check that routine titles match exactly (including emojis, spacing)
- Verify your routines are saved in Hevy, not just workout history
- Make sure HEVY_API_KEY environment variable is set
- Run with debug mode if cycle detection isn't working
""" 