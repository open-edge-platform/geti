// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { getMockedDatasetIdentifier } from '../../../test-utils/mocked-items-factory/mocked-identifiers';

export const getUseCameraParams = ({ ...options } = {}) => ({
    defaultLabelId: '',
    hasDefaultLabel: false,
    isLivePrediction: false,
    isPhotoCaptureMode: true,
    ...getMockedDatasetIdentifier(),
    ...options,
});
