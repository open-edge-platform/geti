// Copyright (C) 2025 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

import type { TaskType } from '@/api/types';

export type TaskOption = {
    id: string;
    imageSrc: string;
    titleKey: string;
    descriptionKey: string;
    adviceKey: string;
    verbKey: string;
    value: TaskType;
};
