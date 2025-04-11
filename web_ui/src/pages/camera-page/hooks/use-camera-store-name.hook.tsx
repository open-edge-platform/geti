// INTEL CONFIDENTIAL
//
// Copyright (C) 2024 Intel Corporation
//
// This software and the related documents are Intel copyrighted materials, and your use of them is governed by
// the express license under which they were provided to you ("License"). Unless the License provides otherwise,
// you may not use, modify, copy, publish, distribute, disclose or transmit this software or the related documents
// without Intel's prior written permission.
//
// This software and the related documents are provided as is, with no express or implied warranties,
// other than those that are expressly stated in the License.

import isEmpty from 'lodash/isEmpty';
import { useMatch } from 'react-router-dom';

import { paths } from '../../../core/services/routes';
import { useCameraParams } from './camera-params.hook';

export const useCameraStoreName = () => {
    const livePredictionPageMatch = useMatch(paths.project.tests.livePrediction.pattern);
    const { isLivePrediction: isLivePredictionParam, projectId, datasetId } = useCameraParams();
    const isLivePredictionTestPage = !isEmpty(livePredictionPageMatch);

    if (isLivePredictionParam || isLivePredictionTestPage) {
        return `project-live-inference-${projectId}`;
    }

    return `dataset-${datasetId}`;
};
