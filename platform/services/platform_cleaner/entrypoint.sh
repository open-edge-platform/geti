#!/bin/bash 

# Copyright (C) 2022-2025 Intel Corporation
# LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

PYTHONPATH=. python3.10 platform_cleaner.py
#!/bin/bash 

# Copyright (C) 2022-2025 Intel Corporation
# LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

if [ "$1" == "platform_cleaner" ]; then
    PYTHONPATH=. python3.10 platform_cleaner.py
elif [ "$1" == "delete_not_activated_users" ]; then
    PYTHONPATH=. python3.10 delete_not_activated_users/delete_not_activated_users.py
else
    echo "Usage: $0 {platform_cleaner|delete_not_activated_users}"
    exit 1
fi
