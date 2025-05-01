// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { Key, useMemo } from 'react';

import { hasEqualId } from '@shared/utils';
import { useNavigate } from 'react-router-dom';

import { ModelsGroups, ModelVersion } from '../../../../../../core/models/models.interface';
import { paths } from '../../../../../../core/services/routes';
import { useModelIdentifier } from '../../../../../../hooks/use-model-identifier/use-model-identifier.hook';

export const useSelectedModel = (
    modelGroup: ModelsGroups | undefined
): [ModelVersion | undefined, (modelVersion: Key) => void] => {
    const { workspaceId, projectId, modelId, groupId, organizationId } = useModelIdentifier();
    const navigate = useNavigate();

    const selectedModel = useMemo<ModelVersion | undefined>(
        () => modelGroup?.modelVersions.find(hasEqualId(modelId)),
        [modelGroup, modelId]
    );

    const handleSelectModel = (modelVersion: Key): void => {
        const newSelectedModel = modelGroup?.modelVersions.find(({ version }) => version === Number(modelVersion));

        if (newSelectedModel === undefined || newSelectedModel.id === selectedModel?.id) {
            return;
        }

        const { id } = newSelectedModel;

        navigate(
            paths.project.models.model.index({
                organizationId,
                workspaceId,
                projectId,
                groupId,
                modelId: id,
            })
        );
    };

    return [selectedModel, handleSelectModel];
};
