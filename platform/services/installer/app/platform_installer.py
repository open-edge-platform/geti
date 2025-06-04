# Copyright (C) 2022-2025 Intel Corporation
# LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import logging
import os
import signal
import sys

import rich_click as click

from commands.install import install
from constants.paths import INSTALL_LOG_FILE_PATH

sys.stdout.reconfigure(encoding="utf-8")  # type: ignore[attr-defined, union-attr]


def signal_handler(sig, frame):  # noqa: ANN001, ANN201, ARG001, D103
    sys.stdout.flush()
    click.echo("\nAborted.")
    sys.exit(0)


@click.group()
def cli():  # noqa: ANN201, D103
    pass


if __name__ == "__main__":
    signal.signal(signal.SIGINT, signal_handler)
    os.chdir(os.path.dirname(sys.argv[0]))
    logger = logging.getLogger(__name__)
    cli.add_command(install)

    try:
        cli()
    except Exception as err:
        logger.exception(err)
        click.echo(f"\nUnexpected error occurred. Details can be found in {INSTALL_LOG_FILE_PATH}", err=True)
        sys.exit(1)
