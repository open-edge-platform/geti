// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { useCameraParams } from './camera-params.hook';

export const useCameraStoreName = () => {
    const { datasetId } = useCameraParams();

    return `dataset-${datasetId}`;
};
