import json
from pathlib import Path
import os

# Determine the path for calendar_rules.json
# In a typical Flask app, this might be in an instance folder or configured.
# For this script, as per subtask instructions, we'll place it in the repo root.
# However, utils.py usually relies on app.instance_path or a config variable.
# Let's assume the script is run from the repo root.
rules_file_path_str = "calendar_rules.json"
rules_file_path = Path(rules_file_path_str)

print(f"Attempting to process file at: {rules_file_path.resolve()}")

data = {}
if rules_file_path.exists():
    try:
        with open(rules_file_path, "r", encoding="utf-8") as f:
            content = f.read()
            if not content.strip(): # File is empty
                print(f"'{rules_file_path_str}' is empty. Initializing with default structure.")
                data = {}
            else:
                data = json.loads(content)
        if not isinstance(data, dict): # Ensure root is a dictionary
            print(f"'{rules_file_path_str}' does not contain a valid JSON object. Re-initializing.")
            data = {}
    except json.JSONDecodeError:
        print(f"Error decoding JSON from '{rules_file_path_str}'. Re-initializing.")
        data = {}
    except Exception as e:
        print(f"An unexpected error occurred while reading '{rules_file_path_str}': {e}. Re-initializing.")
        data = {}
else:
    print(f"'{rules_file_path_str}' does not exist. Creating with default structure.")
    data = {}

# Ensure specialized_requirements key exists and is a dictionary
if "specialized_requirements" not in data or not isinstance(data.get("specialized_requirements"), dict):
    print(f"'specialized_requirements' key missing or not a dict. Initializing.")
    data["specialized_requirements"] = {}

# Define default top-level rule structure (similar to utils.py DEFAULT_RULES and DEFAULT_DEFINED_ATTRIBUTES)
default_top_level_keys = {
    "max_consecutive_days": 5,
    "min_staff_per_day": 1,
    "forbidden_pairs": [],
    "required_pairs": [],
    "required_attributes": {},
    "employee_attributes": {},
    "defined_attributes": ["Dog", "Lady", "Man", "Kaji", "Massage"], # from utils.DEFAULT_DEFINED_ATTRIBUTES
    # specialized_requirements is handled above
}

# Ensure other default top-level keys exist if not present
updated_keys = False
for key, default_value in default_top_level_keys.items():
    if key not in data:
        print(f"Adding missing default key: '{key}'")
        data[key] = default_value
        updated_keys = True
    elif key == "defined_attributes" and (not isinstance(data[key], list) or not all(isinstance(attr, str) for attr in data[key])):
        # Ensure defined_attributes is a list of strings if it exists but is malformed
        print(f"Correcting malformed 'defined_attributes' key.")
        data[key] = default_value
        updated_keys = True


try:
    with open(rules_file_path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    print(f"Successfully updated '{rules_file_path_str}'.")
    if "specialized_requirements" in data and isinstance(data["specialized_requirements"], dict):
        print("Confirmed 'specialized_requirements' key exists and is a dictionary.")
    else:
        print("Error: 'specialized_requirements' key is still missing or not a dictionary after update!")
except Exception as e:
    print(f"An error occurred while writing to '{rules_file_path_str}': {e}")

# Verify by reading back (optional, for script's self-check)
try:
    with open(rules_file_path, "r", encoding="utf-8") as f:
        verify_data = json.load(f)
        print("Verification read successful.")
        if "specialized_requirements" in verify_data and isinstance(verify_data["specialized_requirements"], dict):
            print("Verified: 'specialized_requirements' is present and is a dict.")
        else:
            print("Verification Error: 'specialized_requirements' missing or not a dict in re-read file.")
        # print("Current file content for verification:")
        # print(json.dumps(verify_data, ensure_ascii=False, indent=2))
except Exception as e:
    print(f"Error during verification read: {e}")
