// INTEL CONFIDENTIAL
//
// Copyright (C) 2021 Intel Corporation
//
// This software and the related documents are Intel copyrighted materials, and your use of them is governed by
// the express license under which they were provided to you ("License"). Unless the License provides otherwise,
// you may not use, modify, copy, publish, distribute, disclose or transmit this software or the related documents
// without Intel's prior written permission.
//
// This software and the related documents are provided as is, with no express or implied warranties,
// other than those that are expressly stated in the License.

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
