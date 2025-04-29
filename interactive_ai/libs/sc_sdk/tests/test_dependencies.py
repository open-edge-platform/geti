# Copyright (C) 2022-2025 Intel Corporation
# LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE


import ast
import glob
import os
import shutil
import tempfile

import pytest


def get_module_usages_in_file(path):
    with open(path) as fh:
        root = ast.parse(fh.read(), path)
    result = set()
    for node in ast.iter_child_nodes(root):
        if isinstance(node, ast.Import):
            result.add(node.names[0].name)
        elif isinstance(node, ast.ImportFrom):
            result.add(node.module.split(".")[0])
    return result


@pytest.mark.ScSdkComponent
class TestDependencies:
    def test_module_function(self, request) -> None:
        scratch_file = tempfile.mktemp(prefix="sc_imports", suffix=".py")
        request.addfinalizer(lambda: shutil.rmtree(scratch_file, ignore_errors=True))
        with open(scratch_file, "w") as f:
            f.write("import vegetable\nfrom fruit import banana\n")
        imports = get_module_usages_in_file(scratch_file)
        check_list = ["vegetable", "fruit"]
        negative_results = {}
        for element in check_list:
            if element not in imports:
                negative_results[element] = f"Expected test function to detect import of {element}"
            assert len(negative_results) == 0, f"{negative_results}"

    def test_imports_sdk_to_others(self) -> None:
        sdk_root = os.path.abspath(os.path.join(os.path.dirname(__file__), os.path.pardir))
        py_files = glob.glob(f"{sdk_root}/**/*.py")
        print(len(py_files))
        check_list = ["sc", "tasks", "examples"]
        for file in py_files:
            imports = get_module_usages_in_file(file)
            imports_string = ", ".join(imports)
            print(f"{file} imports {imports_string}")
            negative_results = {}
            for element in check_list:
                if element not in check_list:
                    negative_results[element] = (
                        f"It's not allowed to make imports to the {element} domain from the SDK in file `{file}`"
                    )
            assert len(negative_results) == 0, f"{negative_results}"
