// Copyright (C) 2025-2026 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

import { useState } from 'react';

import { Button, FileTrigger, Flex, Switch, Text, TextField } from '@geti-ui/ui';
import { Checkmark, CloseSmall } from '@geti-ui/ui/icons';
import { clsx } from 'clsx';

import type { VideoFileSourceConfig } from '../../../../constants/shared-types';
import { getErrorMessage } from '../../../../query-client/query-client';
import { ThreeDotsFlashing } from '../../../../shared/components/three-dots-flashing/three-dots-flashing.component';
import { acceptedVideoExtensions } from '../../../dataset/gallery/utils';
import { useUploadSourceMedia } from '../hooks/use-source-mutation.hook';

import classes from './video-file.module.scss';

type VideoFileProps = {
    defaultState?: VideoFileSourceConfig;
};

const ACCEPTED_VIDEO_EXTENSIONS = [acceptedVideoExtensions, '.flv', '.wmv', '.mpg', '.mpeg'];

export const VideoFile = ({ defaultState }: VideoFileProps) => {
    const [videoPath, setVideoPath] = useState(defaultState?.video_path ? String(defaultState.video_path) : '');
    const [isPathTouched, setIsPathTouched] = useState(false);

    const uploadMutation = useUploadSourceMedia();

    const pathError = isPathTouched && videoPath.trim() === '' ? 'Video file path is required' : undefined;

    const handlePathChange = (value: string) => {
        setVideoPath(value);
        uploadMutation.reset();
    };

    const handleFileSelect = async (files: FileList | null) => {
        const file = files?.[0];

        if (!file) {
            return;
        }

        const formData = new FormData();
        formData.append('file', file);

        try {
            const result = await uploadMutation.mutateAsync({
                // @ts-expect-error There is an incorrect type in OpenAPI
                body: formData,
            });

            setVideoPath(result.video_path);
        } catch {
            // Error state is handled via uploadMutation.isError
        }
    };

    return (
        <Flex direction='column' gap='size-200'>
            <TextField isHidden label='id' name='id' defaultValue={defaultState?.id} />
            <TextField width='100%' label='Name' name='name' defaultValue={defaultState?.name} />

            <Flex direction='column' gap='size-100'>
                <Flex
                    gap='size-100'
                    alignItems='end'
                    UNSAFE_className={clsx(classes.pathRow, { [classes.hasError]: pathError !== undefined })}
                >
                    <TextField
                        isRequired
                        flex='1'
                        name='video_path'
                        label='Video file path'
                        value={videoPath}
                        onChange={handlePathChange}
                        onBlur={() => setIsPathTouched(true)}
                        errorMessage={pathError}
                        validationState={pathError === undefined ? undefined : 'invalid'}
                    />

                    <FileTrigger
                        data-testid='upload-video-file'
                        acceptedFileTypes={ACCEPTED_VIDEO_EXTENSIONS}
                        onSelect={handleFileSelect}
                    >
                        <Button variant='secondary' isDisabled={uploadMutation.isPending}>
                            Upload
                        </Button>
                    </FileTrigger>
                </Flex>

                {uploadMutation.isPending && (
                    <Flex alignItems='center' gap='size-100'>
                        <Text>Uploading</Text>
                        <ThreeDotsFlashing />
                    </Flex>
                )}

                {uploadMutation.isSuccess && (
                    <Flex alignItems='center' gap='size-100'>
                        <Checkmark size='S' UNSAFE_className={classes.successIcon} />
                        <Text>Uploaded</Text>
                    </Flex>
                )}

                {uploadMutation.isError && (
                    <Flex alignItems='center' gap='size-100'>
                        <CloseSmall className={classes.errorIcon} />
                        <Text>Upload failed: {getErrorMessage(uploadMutation.error)}</Text>
                    </Flex>
                )}
            </Flex>

            <Switch
                aria-label='loop video'
                name='loop'
                defaultSelected={defaultState?.loop}
                key={defaultState?.loop ? 'true' : 'false'}
            >
                Loop video
            </Switch>
        </Flex>
    );
};
