// Copyright (C) 2025-2026 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

import { useRef } from 'react';

import { UploadProgress } from '@/components/upload-progress/upload-progress.component';
import { useTranslation } from '@/i18n';
import { Button, Flex, Switch, Text, TextField } from '@geti-ui/ui';

import { acceptedVideoExtensions } from '../../../../shared/media-file-utils';
import type { VideoFileUploadProgress } from './api/use-upload-video-file.hook';
import type { VideoFileFormState } from './utils';

import classes from './video-file.module.scss';

interface VideoFileFieldsProps<T extends VideoFileFormState> {
    value: T;
    onChange: (next: T) => void;
    file: File | null;
    onFileChange: (file: File | null) => void;
    uploadProgress: VideoFileUploadProgress | null;
    onCancelUpload: () => void;
}

const ACCEPTED_VIDEO_EXTENSIONS = [acceptedVideoExtensions, '.flv', '.wmv', '.mpg', '.mpeg'].join(',');

export const VideoFileFields = <T extends VideoFileFormState>({
    value,
    onChange,
    file,
    onFileChange,
    uploadProgress,
    onCancelUpload,
}: VideoFileFieldsProps<T>) => {
    const { t } = useTranslation();
    const fileInputRef = useRef<HTMLInputElement>(null);

    const handlePathChange = (videoPath: string) => {
        onChange({ ...value, video_path: videoPath });
        onFileChange(null);
    };

    const handleFileChange = (selectedFile: File | undefined) => {
        if (selectedFile === undefined) return;

        onFileChange(selectedFile);
        onChange({ ...value, video_path: '' });
    };

    return (
        <Flex direction='column' gap='size-200'>
            <TextField
                width='100%'
                label={t('common.labels.name')}
                value={value.name}
                onChange={(name) => onChange({ ...value, name })}
            />

            <Flex direction='column' gap='size-100'>
                <Flex gap='size-100' alignItems='end'>
                    <TextField
                        isRequired={file === null}
                        flex='1'
                        label={t('inference.sources.fields.videoFilePath')}
                        value={value.video_path}
                        onChange={handlePathChange}
                    />

                    <input
                        ref={fileInputRef}
                        type='file'
                        hidden
                        data-testid='upload-video-file'
                        accept={ACCEPTED_VIDEO_EXTENSIONS}
                        onChange={(event) => {
                            handleFileChange(event.target.files?.[0]);

                            event.target.value = '';
                        }}
                    />
                    <Button variant='secondary' onPress={() => fileInputRef.current?.click()}>
                        {t('common.actions.upload')}
                    </Button>
                </Flex>

                {file !== null && (
                    <Flex alignItems='center' gap='size-100'>
                        <Text UNSAFE_className={classes.selectedRow}>
                            {t('inference.sources.fields.selectedFile', { fileName: file.name })}
                        </Text>
                    </Flex>
                )}

                {uploadProgress && (
                    <UploadProgress
                        bytesSent={uploadProgress.bytesSent}
                        bytesTotal={uploadProgress.bytesTotal}
                        onCancel={uploadProgress.bytesSent < uploadProgress.bytesTotal ? onCancelUpload : undefined}
                    />
                )}
            </Flex>

            <Switch
                isEmphasized
                aria-label='loop video'
                isSelected={value.loop}
                onChange={(loop) => onChange({ ...value, loop })}
            >
                {t('inference.sources.fields.loopVideo')}
            </Switch>
        </Flex>
    );
};
