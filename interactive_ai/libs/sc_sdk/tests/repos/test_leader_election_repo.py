# Copyright (C) 2022-2025 Intel Corporation
# LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

from time import sleep

import pytest

from sc_sdk.repos.leader_election_repo import LeaderElectionRepo


@pytest.mark.ScSdkComponent
class TestLeaderElectionRepo:
    def test_stand_for_election(
        self,
    ) -> None:
        """
        <b>Description:</b>
        Check that stand for election only allows one document with TTL for one metric

        <b>Input data:</b>
        None

        <b>Expected results:</b>
        A new leader for a resource is only accepted if no leader exists for that time frame

        <b>Steps</b>
        1. Request leadership for a metric for resource A - accepted
        2. Request leadership for a metric for resource B - denied, A is already leader
        3. Request leadership for a metric for resource A (1 sec) - accepted, TTL is updated to 1 sec
        4. Wait max 60 sec
        5. Request leadership for a metric for resource B - accepted, A is no longer leader
        """

        # Documents will be removed within 60s after expiration date
        # To avoid slow unit tests, only enable if there is reason to believe
        # the TTL mechanism is broken
        test_ttl_mechanism = False

        leader_repo = LeaderElectionRepo()

        assert leader_repo.stand_for_election(subject="A", resource="test_metric", validity_in_seconds=60)
        assert not leader_repo.stand_for_election(subject="B", resource="test_metric", validity_in_seconds=60)
        assert leader_repo.stand_for_election(subject="A", resource="test_metric", validity_in_seconds=0)

        if test_ttl_mechanism:
            for i in range(60):
                if leader_repo.stand_for_election(subject="B", resource="test_metric", validity_in_seconds=0):
                    break
                sleep(1)
            else:
                assert leader_repo.stand_for_election(subject="B", resource="test_metric", validity_in_seconds=0), (
                    "Expected B to claim leadership within 60 seconds of expiration date of leadership A"
                )
