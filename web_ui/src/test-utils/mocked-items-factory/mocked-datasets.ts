// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

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
