# Copyright (C) 2022-2025 Intel Corporation
# LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

from collections.abc import Callable
from concurrent import futures


class ConcurrentUsers:
    def __init__(self, users_count: int, func: Callable):
        self.users_count = users_count
        self.func = func
        self.pool = futures.ThreadPoolExecutor(users_count)

    def start_and_wait(self):
        tasks = []
        for i in range(self.users_count):
            task = self.pool.submit(self.func)
            tasks.append(task)

        futures.wait(tasks, return_when=futures.ALL_COMPLETED)
