# Copyright (C) 2022-2025 Intel Corporation
# LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import pytest

from sc_sdk.utils.concurrency import TimeoutLock


@pytest.mark.ScSdkComponent
class TestTimeoutLock:
    def test_timeout_lock(self) -> None:
        """
        Test the TimeoutLock class

        Steps:
         1. Instantiate the lock
         2. Check that the lock can be explicitly acquired and released
         3. Check that the lock can be acquired via context manager, and
            implicitly released
         4. Check that a TimeoutError is raised when the lock is already taken
        """
        timeout_lock = TimeoutLock(timeout=0.001)
        assert not timeout_lock._lock.locked()  # type: ignore

        timeout_lock.acquire()
        assert timeout_lock._lock.locked()  # type: ignore
        timeout_lock.release()
        assert not timeout_lock._lock.locked()  # type: ignore

        with timeout_lock:
            assert timeout_lock._lock.locked()  # type: ignore
        assert not timeout_lock._lock.locked()  # type: ignore

        timeout_lock.acquire()
        with pytest.raises(TimeoutError), timeout_lock:
            pass
        timeout_lock.release()
