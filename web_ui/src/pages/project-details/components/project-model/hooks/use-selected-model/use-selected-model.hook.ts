// INTEL CONFIDENTIAL
//
// Copyright (C) 2022 Intel Corporation
//
// This software and the related documents are Intel copyrighted materials, and your use of them is governed by
// the express license under which they were provided to you ("License"). Unless the License provides otherwise,
// you may not use, modify, copy, publish, distribute, disclose or transmit this software or the related documents
// without Intel's prior written permission.
//
// This software and the related documents are provided as is, with no express or implied warranties,
// other than those that are expressly stated in the License.

import { Key, useMemo } from 'react';

import { useNavigate } from 'react-router-dom';

import { ModelsGroups, ModelVersion } from '../../../../../../core/models/models.interface';
import { paths } from '../../../../../../core/services/routes';
import { useModelIdentifier } from '../../../../../../hooks/use-model-identifier/use-model-identifier.hook';
import { hasEqualId } from '../../../../../../shared/utils';

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
