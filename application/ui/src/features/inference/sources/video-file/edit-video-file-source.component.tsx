// Copyright (C) 2026 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

import type { VideoFileSourceConfig } from '@/api/types';

import { EditSource } from '../deprecated/edit-source/edit-source.component';
import { useVideoFileUpload } from '../deprecated/video-file/use-video-file-upload.hook';
import { videoFileBodyFormatter } from '../deprecated/video-file/utils';
import { VideoFile } from '../deprecated/video-file/video-file.component';
import type { EditSourceProps } from '../types';

export const EditVideoFileSource = ({
    source,
    isConnected,
    onSaved,
    onBackToList,
}: EditSourceProps<VideoFileSourceConfig>) => {
    const videoFileUpload = useVideoFileUpload();

    return (
        <EditSource
            config={source}
            isConnected={isConnected}
            onSaved={onSaved}
            onBackToList={onBackToList}
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
