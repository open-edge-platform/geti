// Copyright (C) 2026 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

import { useTranslation } from '@/i18n';

import { AddSource } from '../deprecated/add-source/add-source.component';
import { useVideoFileUpload } from '../deprecated/video-file/use-video-file-upload.hook';
import { getVideoFileInitialConfig, videoFileBodyFormatter } from '../deprecated/video-file/utils';
import { VideoFile } from '../deprecated/video-file/video-file.component';
import type { AddSourceProps } from '../types';

export const AddVideoFileSource = ({ existingNames, onSaved }: AddSourceProps) => {
    const { t } = useTranslation();
    const videoFileUpload = useVideoFileUpload();

    return (
        <AddSource
            onSaved={onSaved}
            config={getVideoFileInitialConfig(t, existingNames)}
            componentFields={(state) => (
                <VideoFile
                    defaultState={state}
                    uploadProgress={videoFileUpload.progress}
                    onCancelUpload={videoFileUpload.cancel}
                />
            )}
            bodyFormatter={videoFileBodyFormatter}
            prepareFormData={videoFileUpload.prepareFormData}
        />
    );
};
