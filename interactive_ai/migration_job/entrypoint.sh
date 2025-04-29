#!/bin/bash

# Copyright (C) 2022-2025 Intel Corporation
# LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

echo "=== Running migrations script ==="
echo "target_version: ${TARGET_VERSION}"
echo "current_version: ${CURRENT_VERSION}"

exec "$@"
