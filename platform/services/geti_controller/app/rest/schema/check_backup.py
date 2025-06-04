# Copyright (C) 2022-2025 Intel Corporation
# LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE


from pydantic import BaseModel


class CheckBackupResponse(BaseModel):
    is_backup_possible: bool
