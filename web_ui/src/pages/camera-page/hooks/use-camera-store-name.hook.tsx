// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { paths } from '@geti/core/src/services/routes';
import { isEmpty } from 'lodash-es';
import { useMatch } from 'react-router-dom';

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
