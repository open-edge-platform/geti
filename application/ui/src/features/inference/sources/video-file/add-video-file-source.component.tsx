// Copyright (C) 2026 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

import { useState, type FormEvent } from 'react';

import { useTranslation } from '@/i18n';
import { Flex, Form } from '@geti-ui/ui';
import { useConnectSourceToPipeline } from 'hooks/api/pipeline.hook';

import { AddSourceButton } from '../add-source/add-source-button.component';
import { useCreateSource } from '../api/use-create-source';
import type { AddSourceProps } from '../types';
import { useDeleteSourceVideo } from './api/use-delete-source-video.hook';
import { useUploadVideoFile } from './api/use-upload-video-file.hook';
import { getVideoFileInitialConfig, type VideoFileFormState } from './utils';
import { VideoFileFields } from './video-file-fields.component';

export const AddVideoFileSource = ({ existingNames, onSaved }: AddSourceProps) => {
    const { t } = useTranslation();
    const [config, setConfig] = useState<VideoFileFormState>(() => getVideoFileInitialConfig(t, existingNames));
    const [file, setFile] = useState<File | null>(null);
    const upload = useUploadVideoFile();
    const deleteVideo = useDeleteSourceVideo();
    const createSource = useCreateSource();
    const connectSource = useConnectSourceToPipeline();

    const handleSubmit = async (event: FormEvent) => {
        event.preventDefault();

        try {
            const uploaded = file ? await upload.mutateAsync(file) : null;
            const { id } = await createSource
                .mutateAsync({ body: { ...config, video_path: uploaded?.videoPath ?? config.video_path } })
                .catch((error: unknown) => {
                    // Best effort: the upload is orphaned once the source is not created.
                    if (uploaded?.mediaId) deleteVideo.mutate(uploaded.mediaId);
                    throw error;
                });
            await connectSource.mutateAsync(String(id));
            onSaved();
        } catch {
            // toasts are handled by the hooks / MutationCache
        }
    };

    return (
        <Form validationBehavior='native' onSubmit={handleSubmit}>
            <Flex gap='size-200' direction='column'>
                <VideoFileFields
                    value={config}
                    onChange={setConfig}
                    file={file}
                    onFileChange={setFile}
                    uploadProgress={upload.progress}
                    onCancelUpload={upload.cancel}
                />

                <AddSourceButton
                    isPending={upload.isPending || createSource.isPending || connectSource.isPending}
                    isDisabled={
                        config.name.trim().length === 0 || (file === null && config.video_path.trim().length === 0)
                    }
                />
            </Flex>
        </Form>
    );
};
