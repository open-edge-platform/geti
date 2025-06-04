#!/bin/bash 

# Copyright (C) 2022-2025 Intel Corporation
# LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

PYTHONPATH=. python3.10 -m uvicorn main:app --port 9200 --host 0.0.0.0 --log-config logconfig.ini
