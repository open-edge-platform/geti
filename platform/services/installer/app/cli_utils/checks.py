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
A module containing CLI utilities related to check functions.
"""

import logging
from collections.abc import Callable

import rich_click as click

from checks.errors import CheckError, CheckIgnored, CheckSkipped, CheckWarning, CumulativeCheckError
from cli_utils.spinner import click_spinner

logger = logging.getLogger(__name__)

CROSS_MARK = "\u274c"
CROSS_WARNING = "\u2717"
SKIP_MESSAGE = "SKIPPED"
TICK_MARK = "\u2714"


def resolve_check_function_name(check_function: Callable) -> str:
    """
    Return the name of check function.
    """
    try:
        return check_function.__name__
    except AttributeError:
        # Get check_name for partial functions,
        # mypy check ignored due to: https://github.com/python/mypy/issues/1484
        return check_function.func.__name__  # type: ignore


def _run_check(check_function: Callable):
    with click_spinner.spinner() as spinner:
        check_function_name = resolve_check_function_name(check_function)
        logger.info(f"Running check: {check_function_name}")
        try:
            # only needed for functions, where
            # spinner manipulation is required
            check_function(spinner=spinner)
        except TypeError:
            check_function()


def run_checks(checks: list[tuple[str, Callable]]):  # noqa: ANN201
    """
    Takes a list of checks as a tuples of check message and check function.
    For each check, check message is displayed together with spinner and check function is executed.
    If check function is successful, green tick mark is sign to the user, in case of error a red cross mark is shown
    together with error message.
    """
    failed_checks = []
    for check_message, check_function in checks:
        try:
            click.echo(check_message, nl=False)
            try:
                _run_check(check_function=check_function)
                click.secho(f" {TICK_MARK}", fg="green")
            except CheckSkipped:
                click.echo(f" {SKIP_MESSAGE}")
            except CheckIgnored:
                pass
        except CheckWarning as warning:
            logger.debug(str(warning))
            click.secho(f" {CROSS_WARNING}", fg="yellow")
            click.secho(warning, fg="yellow")
        except CheckError as error:
            logger.debug(str(error))
            click.secho(f" {CROSS_MARK}", fg="red")
            click.secho(error, fg="red")
            failed_checks.append(error)

    if failed_checks:
        raise CumulativeCheckError(exceptions=failed_checks)
