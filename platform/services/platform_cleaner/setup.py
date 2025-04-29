# Copyright (C) 2022-2025 Intel Corporation
# LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

from setuptools import find_packages, setup

__version__ = "1.0.0"

install_requires = []

try:
    with open("requirements.txt") as f:
        for line in f:
            req_line = line.strip()
            if req_line and not req_line.startswith("#"):
                install_requires.append(req_line)
except FileNotFoundError:
    pass

setup(
    name="platform_cleaner",
    version=__version__,
    packages=find_packages(exclude=["*tests"]),
    install_requires=install_requires,
    entry_points={
        "console_scripts": [
            "platform_cleaner = platform_cleaner.platform_cleaner:main",
            "delete_not_activated_users = platform_cleaner.delete_not_activated_users.delete_not_activated_users:main",
        ]
    },
)
