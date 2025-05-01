// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { Button } from '@shared/components/button/button.component';
import { getIds } from '@shared/utils';
import { v4 as uuid } from 'uuid';

import { Label } from '../../../../core/labels/label.interface';
import { useCameraStorage } from '../../hooks/use-camera-storage.hook';
import { validateVideoDimensions } from '../../media-validation-utils';
import { useVideoRecording, VideoFormat } from '../../providers/video-recording-provider.component';

import classes from './action-buttons.module.scss';

interface CaptureVideoButtonProps {
    selectedLabels: Label[];
}

export const CaptureVideoButton = ({ selectedLabels }: CaptureVideoButtonProps) => {
    const fileId = uuid();
    const { saveMedia } = useCameraStorage();
    const { recordingConfig, isRecording } = useVideoRecording();

    const { startRecording, stopRecording } = recordingConfig({
        name: fileId,
        format: VideoFormat.WEBM,
        onVideoReady: validateVideoDimensions((video: File) => {
            const labelName = selectedLabels.at(-1)?.name ?? null;

            // @ts-expect-error video is disabled at the moment
            // TODO: update types after video is enabled
            saveMedia({ id: fileId, file: video, labelIds: getIds(selectedLabels), labelName });
        }),
    });

    return (
        <Button
            variant={'primary'}
            aria-label={'video capture'}
            UNSAFE_className={[classes.videoButton, isRecording ? classes.recordingButton : ''].join(' ')}
            onPress={isRecording ? stopRecording : startRecording}
        >
            <div></div>
        </Button>
    );
};
