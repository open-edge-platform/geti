// Copyright (C) 2025 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

import type { Label } from '@/api/types';
import { useProject } from 'hooks/api/project.hook';

export const useProjectLabels = (): Label[] => {
    const { data: project } = useProject();

    return project.task.labels || [];
};
