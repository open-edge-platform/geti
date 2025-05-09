# Copyright (C) 2022-2025 Intel Corporation
# LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE
"""
This script takes a Makefile target as input and a list of files.
Then it executes this Makefile target in every Python project (identified by the presence of a pyproject.toml).
When calling the Makefile, it passes the list of files as a variable called FILES.
"""

import sys
import os
import glob
from pathlib import Path
from collections import defaultdict
import subprocess

make_target = sys.argv[1]
changed_files = sys.argv[2:]

pyproject_files = glob.glob("**/pyproject.toml", recursive=True)
project_dirs = {str(Path(file).parent) for file in pyproject_files}

# Group the changed_files by project_dir.
# Instead of matching every file with every project directory with quadratic complexity,
# we sort the list of files and directories which allow us to group in logarithmic complexity.
files_per_project = defaultdict(list)
paths = sorted(changed_files + list(project_dirs))

current_project_dir = None

for path in paths:
    if path in project_dirs:
        current_project_dir = path
    elif current_project_dir is not None and path.startswith(current_project_dir):
        files_per_project[current_project_dir].append(path)
    else:
        print(f"Warning: the file {path} does not belong to any Python project.")

# Prevent warnings from uv due to the pre-commit virtual env.
del os.environ["VIRTUAL_ENV"]

exit_code = 0

for project_dir, project_files in files_per_project.items():
    if subprocess.run(
        ["make", "-n", make_target],
        cwd=project_dir,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    ).returncode:
        print(
            f"Skipping {project_dir} because the Makefile has no target {make_target}."
        )
    else:
        print(f"Executing target {make_target} in {project_dir}...")
        project_files = [
            str(Path(file).relative_to(project_dir)) for file in project_files
        ]
        exit_code |= subprocess.run(
            ["make", make_target, "FILES=" + " ".join(project_files)], cwd=project_dir
        ).returncode

sys.exit(exit_code)
