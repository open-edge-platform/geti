# Copyright (C) 2026 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

"""Skip all Hugging Face tests when the optional huggingface extra is not installed."""

import pytest

pytest.importorskip("transformers", reason="transformers is not installed")
pytest.importorskip("accelerate", reason="accelerate is not installed")
