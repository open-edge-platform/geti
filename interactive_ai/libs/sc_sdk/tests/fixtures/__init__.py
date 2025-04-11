# INTEL CONFIDENTIAL
#
# Copyright (C) 2023 Intel Corporation
#
# This software and the related documents are Intel copyrighted materials, and
# your use of them is governed by the express license under which they were provided to
# you ("License"). Unless the License provides otherwise, you may not use, modify, copy,
# publish, distribute, disclose or transmit this software or the related documents
# without Intel's prior written permission.
#
# This software and the related documents are provided as is,
# with no express or implied warranties, other than those that are expressly stated
# in the License.
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
