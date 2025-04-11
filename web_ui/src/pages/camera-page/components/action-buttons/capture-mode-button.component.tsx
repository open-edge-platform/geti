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

import { ButtonGroup } from '@adobe/react-spectrum';
import { useSearchParams } from 'react-router-dom';

import { useFeatureFlags } from '../../../../core/feature-flags/hooks/use-feature-flags.hook';
import { Button } from '../../../../shared/components/button/button.component';
import { CaptureMode, useCameraParams } from '../../hooks/camera-params.hook';

export const CaptureModeButton = () => {
    const { isPhotoCaptureMode } = useCameraParams();
    const [searchParams, setSearchParams] = useSearchParams();
    const { FEATURE_FLAG_CAMERA_VIDEO_UPLOAD } = useFeatureFlags();

    const handleToggleMode = (mode: CaptureMode) => {
        searchParams.set('captureMode', mode);
        setSearchParams(searchParams);
    };

    if (!FEATURE_FLAG_CAMERA_VIDEO_UPLOAD) {
        return <></>;
    }

    return (
        <ButtonGroup>
            <Button
                key={CaptureMode.VIDEO}
                aria-label='video mode'
                variant={!isPhotoCaptureMode ? 'accent' : 'secondary'}
                onPress={() => handleToggleMode(CaptureMode.VIDEO)}
            >
                Video
            </Button>
            <Button
                key={CaptureMode.PHOTO}
                marginStart={'size-65'}
                aria-label='photo mode'
                variant={isPhotoCaptureMode ? 'accent' : 'secondary'}
                onPress={() => handleToggleMode(CaptureMode.PHOTO)}
            >
                Photo
            </Button>
        </ButtonGroup>
    );
};
