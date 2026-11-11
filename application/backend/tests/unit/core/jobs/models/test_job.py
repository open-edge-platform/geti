# Copyright (C) 2026 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

from unittest.mock import patch


class TestJob:
    def test_timestamps_are_set_when_the_job_is_created(self, fxt_job):
        with patch("app.core.jobs.models.job.datetime") as mock_datetime:
            mock_datetime.now.return_value.timestamp.return_value = 123.0
            job = fxt_job()

        assert job.submitted_at == 123.0
        assert job.updated_at == 123.0
