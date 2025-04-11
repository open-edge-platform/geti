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
