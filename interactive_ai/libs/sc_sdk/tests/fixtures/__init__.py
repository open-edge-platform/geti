# Copyright (C) 2022-2025 Intel Corporation
# LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE
import pathlib


def import_all_fixtures(__init__py__file__: str):
    """
    Import all fixtures methods from __init__py__file__ parent directory
    :param __init__py__file__: __init__.py file provided as a __file__
    :return: None
    """
    for fixture_module in pathlib.Path(__init__py__file__).resolve().parent.iterdir():
        if not fixture_module.stem.endswith("__"):
            module = __import__(fixture_module.stem, globals(), locals(), fromlist=["*"], level=1)
            if hasattr(module, "__all__"):
                all_names = module.__all__
            else:
                all_names = [name for name in dir(module) if not name.startswith("_")]
            globals().update({name: getattr(module, name) for name in all_names})


import_all_fixtures(__file__)
