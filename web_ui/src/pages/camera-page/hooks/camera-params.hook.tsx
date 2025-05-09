// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { isNil } from 'lodash-es';
import { useSearchParams } from 'react-router-dom';

import { useFeatureFlags } from '../../../core/feature-flags/hooks/use-feature-flags.hook';
import { useDatasetIdentifier } from '../../annotator/hooks/use-dataset-identifier.hook';

export enum CaptureMode {
    PHOTO = 'photo',
    VIDEO = 'video',
}

export const useCameraParams = () => {
    const [searchParams] = useSearchParams();
    const datasetIdentifier = useDatasetIdentifier();
    const { FEATURE_FLAG_CAMERA_VIDEO_UPLOAD } = useFeatureFlags();

    const captureMode = FEATURE_FLAG_CAMERA_VIDEO_UPLOAD ? searchParams.get('captureMode') : CaptureMode.PHOTO;
    const defaultLabelId = searchParams.get('defaultLabelId');

    return {
        ...datasetIdentifier,
        defaultLabelId: defaultLabelId ? defaultLabelId : null,
        hasDefaultLabel: !isNil(defaultLabelId) && defaultLabelId !== 'undefined',
        isLivePrediction: searchParams.get('isLivePrediction') === 'true',
        isPhotoCaptureMode: captureMode ? captureMode === CaptureMode.PHOTO : true,
    };
};
