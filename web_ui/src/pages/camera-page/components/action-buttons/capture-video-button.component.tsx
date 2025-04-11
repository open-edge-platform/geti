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

import { v4 as uuid } from 'uuid';

import { Label } from '../../../../core/labels/label.interface';
import { Button } from '../../../../shared/components/button/button.component';
import { getIds } from '../../../../shared/utils';
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
