// Copyright (C) 2026 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

import { useRef, useState, type FormEvent } from 'react';

import type { VideoFileSourceConfig } from '@/api/types';
import { Form } from '@geti-ui/ui';
import { useConnectSourceToPipeline } from 'hooks/api/pipeline.hook';
import { isEqual } from 'lodash-es';

import { useUpdateSource } from '../api/use-update-source';
import { EditSourceButtons } from '../edit-source/edit-source-buttons.component';
import { EditSourceFieldsPanel } from '../edit-source/edit-source-fields-panel.component';
import { EditSourceHeader } from '../edit-source/edit-source-header.component';
import type { EditSourceProps } from '../types';
import { useDeleteSourceVideo } from './api/use-delete-source-video.hook';
import { useUploadVideoFile } from './api/use-upload-video-file.hook';
import { VideoFileFields } from './video-file-fields.component';

export const EditVideoFileSource = ({
    source,
    isConnected,
    onSaved,
    onBackToList,
}: EditSourceProps<VideoFileSourceConfig>) => {
    const [config, setConfig] = useState<VideoFileSourceConfig>(source);
    const [file, setFile] = useState<File | null>(null);
    const connectOnSave = useRef(false);
    const upload = useUploadVideoFile();
    const deleteVideo = useDeleteSourceVideo();
    const updateSource = useUpdateSource();
    const connectSource = useConnectSourceToPipeline();

    const handleSubmit = async (event: FormEvent) => {
        event.preventDefault();

        try {
            const uploaded = file ? await upload.mutateAsync(file) : null;
            const { id, source_type, ...fields } = config;
            await updateSource
                .mutateAsync({
                    params: { path: { source_id: id } },
                    body: { ...fields, video_path: uploaded?.videoPath ?? fields.video_path },
                })
                .catch((error: unknown) => {
                    // Best effort: the upload is orphaned once the source is not updated.
                    if (uploaded?.mediaId) deleteVideo.mutate(uploaded.mediaId);
                    throw error;
                });
            if (connectOnSave.current) await connectSource.mutateAsync(id);
            onSaved();
        } catch {
            // toasts are handled by the hooks / MutationCache
        }
    };

    return (
        <Form validationBehavior='native' onSubmit={handleSubmit}>
            <EditSourceHeader onBack={onBackToList} />

            <EditSourceFieldsPanel>
                <VideoFileFields
                    value={config}
                    onChange={setConfig}
                    file={file}
                    onFileChange={setFile}
                    uploadProgress={upload.progress}
                    onCancelUpload={upload.cancel}
                />
            </EditSourceFieldsPanel>

            <EditSourceButtons
                isDisabled={file === null && isEqual(config, source)}
                isPending={upload.isPending || updateSource.isPending || connectSource.isPending}
                isConnected={isConnected}
                onSave={() => (connectOnSave.current = false)}
                onSaveAndConnect={() => (connectOnSave.current = true)}
            />
        </Form>
    );
};
