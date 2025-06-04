# INTEL CONFIDENTIAL
#
# Copyright (C) 2022 Intel Corporation
#
# This software and the related documents are Intel copyrighted materials, and your use of them is governed by
# the express license under which they were provided to you ("License"). Unless the License provides otherwise,
# you may not use, modify, copy, publish, distribute, disclose or transmit this software or the related documents
# without Intel's prior written permission.
#
# This software and the related documents are provided as is, with no express or implied warranties,
# other than those that are expressly stated in the License.

"""
spinner module is a wrapper around click_spinner library which fixes known bug
"""

import click_spinner


def init_spin(self):  # noqa: ANN001, ANN201
    """
    This method overwrite fixes https://github.com/click-contrib/click-spinner/pull/37
    https://jira.devtools.intel.com/browse/CVS-92230
    """
    while not self.stop_running.is_set():
        self.stream.write(next(self.spinner_cycle, "\b"))
        self.stream.write("\b")
        self.stream.flush()
        self.stop_running.wait(0.25)
    self.stream.write(" ")
    self.stream.write("\b")
    self.stream.flush()


click_spinner.Spinner.init_spin = init_spin  # type: ignore
