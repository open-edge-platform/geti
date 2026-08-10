// Copyright (C) 2025 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

import { $api } from '@/api';
import { useProjectIdentifier } from 'hooks/use-project-identifier.hook';

export const useGetModel = (modelId: string | null | undefined, enabled: boolean = true) => {
    const projectId = useProjectIdentifier();

    return $api.useQuery(
        'get',
        '/api/projects/{project_id}/models/{model_id}',
        { params: { path: { project_id: projectId, model_id: String(modelId) } } },
        { enabled }
    );
};
