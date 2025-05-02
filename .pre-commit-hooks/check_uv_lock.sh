#!/bin/bash

set -e

echo "Running 'uv lock --check' on all projects with pyproject.toml..."

# Find all directories containing a pyproject.toml file
PYPROJECT_DIRS=()
while IFS= read -r dir; do
  PYPROJECT_DIRS+=("$dir")
done < <(find . -path "*/.venv" -prune -o -type f -name "pyproject.toml" -exec dirname {} \;)
EXIT_CODE=0

for dir in "${PYPROJECT_DIRS[@]}"; do
  if [ -f "$dir/uv.lock" ]; then
    echo "Checking $dir"
    if ! (cd "$dir" && uv lock --check); then
      echo "❌ uv lock --check failed in $dir"
      EXIT_CODE=1
    fi
  else
    echo "Skipping $dir (no uv.lock found)"
  fi
done

if [ "$EXIT_CODE" -ne 0 ]; then
  echo "One or more 'uv lock --check' checks failed."
  exit $EXIT_CODE
fi

echo "✅ All 'uv lock --check' checks passed."
