// Copyright (C) 2026 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

import { $api } from '@/api';
import { useProjectIdentifier } from 'hooks/use-project-identifier.hook';

export const useGetModelTrainingMetrics = (modelId: string | null | undefined) => {
    const projectId = useProjectIdentifier();

    return $api.useQuery(
        'get',
        '/api/projects/{project_id}/models/{model_id}/training_metrics',
        {
            params: { path: { project_id: projectId, model_id: String(modelId) } },
        },
        { enabled: Boolean(modelId) }
    );
};
