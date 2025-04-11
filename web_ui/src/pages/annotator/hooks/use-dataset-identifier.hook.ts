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

import { DatasetIdentifier } from '../../../core/projects/dataset.interface';
import { useProjectIdentifier } from '../../../hooks/use-project-identifier/use-project-identifier';
import { useSelectedDataset } from '../../project-details/components/project-dataset/use-selected-dataset/use-selected-dataset.hook';

export const useDatasetIdentifier = (): DatasetIdentifier => {
    const { workspaceId, projectId, organizationId } = useProjectIdentifier();
    const selectedDataset = useSelectedDataset();

    return useMemo(() => {
        return {
            organizationId,
            workspaceId,
            projectId,
            datasetId: selectedDataset.id,
        };
    }, [organizationId, workspaceId, projectId, selectedDataset.id]);
};
