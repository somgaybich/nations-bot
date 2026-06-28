# Force-resolve the absolute, physical path of this script file
REAL_SCRIPT_PATH="$(readlink -f "${BASH_SOURCE[0]}")"

# Get the 'bin' directory where the script actually lives
SCRIPT_DIR="$(cd "$(dirname "$REAL_SCRIPT_PATH")" && pwd)"

# Step up to the true project root directory
PROJECT_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"

# Change directory to the root GitHub folder before running Python
cd "$PROJECT_DIR"

"$PROJECT_DIR/.venv/bin/python" "$PROJECT_DIR/core.py" "$@"