// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { Button, ButtonGroup } from '@geti/ui';
import { useSearchParams } from 'react-router-dom';

import { useFeatureFlags } from '../../../../core/feature-flags/hooks/use-feature-flags.hook';
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
