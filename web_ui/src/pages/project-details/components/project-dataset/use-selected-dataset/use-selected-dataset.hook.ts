// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { useMemo } from 'react';

import { useParams } from 'react-router-dom';

import { Dataset, DatasetIdentifierParams } from '../../../../../core/projects/dataset.interface';
import { hasEqualId } from '../../../../../shared/utils';
import { useProject } from '../../../providers/project-provider/project-provider.component';

export const useSelectedDataset = (): Dataset => {
    const { project } = useProject();

    const params = useParams<DatasetIdentifierParams>();

    return useMemo(() => {
        return project.datasets.find(hasEqualId(params.datasetId)) ?? project.datasets[0];
    }, [params.datasetId, project.datasets]);
};
