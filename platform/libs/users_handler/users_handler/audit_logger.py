"""Audit logs utilities"""

# Copyright (C) 2022-2025 Intel Corporation
# LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import logging
import os
from pathlib import Path


class AuditLogger:
    """
    The class contains the base configuration of audit logs formatter and also creates file handler for these logs
    """

    _AUDIT_TMP_LOG_PATH = "/tmp/spicedb_audit.log"  # noqa: S108

    @staticmethod
    def _get_root_formatter() -> logging.Formatter:
        empty_formatter = logging.Formatter()
        if logging.root.handlers:
            root_formatter = logging.root.handlers[0].formatter
            actual_formatter: logging.Formatter = root_formatter if root_formatter is not None else empty_formatter
            return actual_formatter
        return empty_formatter

    @classmethod
    def get_spicedb_file_handler(cls) -> logging.FileHandler:
        """
        Creating a file handler that will contain spiceDB logs and return this formatter
        """
        _path_log_audit: Path = Path(os.getenv("SPICEDB_LOG_PATH", cls._AUDIT_TMP_LOG_PATH))
        spice_db_file_handler = logging.FileHandler(filename=_path_log_audit)
        spice_db_file_handler.setFormatter(cls._get_root_formatter())
        return spice_db_file_handler
