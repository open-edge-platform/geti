// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { useMemo } from 'react';

import { useParams } from 'react-router-dom';

import { ModelIdentifier } from '../../core/models/models.interface';
import { useProjectIdentifier } from '../use-project-identifier/use-project-identifier';

export const useModelIdentifier = (): ModelIdentifier => {
    const { organizationId, workspaceId, projectId } = useProjectIdentifier();
    const { modelId, groupId } = useParams<Pick<ModelIdentifier, 'groupId' | 'modelId'>>() as Pick<
        ModelIdentifier,
        'groupId' | 'modelId'
    >;

    return useMemo(
        () => ({ organizationId, workspaceId, projectId, groupId, modelId }),
        [organizationId, workspaceId, projectId, groupId, modelId]
    );
};
