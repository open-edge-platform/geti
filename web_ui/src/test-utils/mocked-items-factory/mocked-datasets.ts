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

import { Dataset } from '../../core/projects/dataset.interface';
import { DatasetDTO } from '../../core/projects/dtos/project.interface';

export const getMockedDataset = (customValues?: Partial<Dataset>): Dataset => {
    return {
        id: '12345',
        name: 'Training dataset',
        useForTraining: true,
        creationTime: '2022-07-22',
        ...customValues,
    };
};

export const getMockedDatasetDTO = (customValues?: Partial<DatasetDTO>): DatasetDTO => {
    return {
        id: '12345',
        name: 'Testing set',
        use_for_training: false,
        creation_time: '2022-07-22',
        ...customValues,
    };
};
