// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

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
