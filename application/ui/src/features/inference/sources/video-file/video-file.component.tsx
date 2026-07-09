// Copyright (C) 2025-2026 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

import { useRef, useState } from 'react';

import { Button, Flex, Switch, Text, TextField } from '@geti-ui/ui';

import type { VideoFileSourceConfig } from '@/api/types';
import { acceptedVideoExtensions } from '../../../dataset/gallery/utils';

import classes from './video-file.module.scss';

type VideoFileProps = {
    defaultState?: VideoFileSourceConfig;
};

const ACCEPTED_VIDEO_EXTENSIONS = [acceptedVideoExtensions, '.flv', '.wmv', '.mpg', '.mpeg'].join(',');

export const VideoFile = ({ defaultState }: VideoFileProps) => {
    const [videoPath, setVideoPath] = useState(defaultState?.video_path ?? '');
    const [selectedFile, setSelectedFile] = useState<File | null>(null);

    const fileInputRef = useRef<HTMLInputElement>(null);

    // Typing a path and choosing a file are mutually exclusive; the most recent action wins.
    const handlePathChange = (value: string) => {
        setVideoPath(value);
        setSelectedFile(null);

        if (fileInputRef.current) {
            fileInputRef.current.value = '';
        }
    };

    const handleFileChange = (file: File | null) => {
        setSelectedFile(file);

        if (file !== null) {
            setVideoPath('');
        }
    };

    return (
        <Flex direction='column' gap='size-200'>
            <TextField isHidden label='id' name='id' defaultValue={defaultState?.id} />
            <TextField width='100%' label='Name' name='name' defaultValue={defaultState?.name} />

            <Flex direction='column' gap='size-100'>
                <Flex gap='size-100' alignItems='end'>
                    <TextField
                        isRequired={selectedFile === null}
                        flex='1'
                        name='video_path'
                        label='Video file path'
                        value={videoPath}
                        onChange={handlePathChange}
                    />

                    <input
                        ref={fileInputRef}
                        type='file'
                        name='video_file'
                        hidden
                        data-testid='upload-video-file'
                        accept={ACCEPTED_VIDEO_EXTENSIONS}
                        onChange={(event) => handleFileChange(event.target.files?.[0] ?? null)}
                    />
                    <Button variant='secondary' onPress={() => fileInputRef.current?.click()}>
                        Upload
                    </Button>
                </Flex>

                {selectedFile !== null && (
                    <Flex alignItems='center' gap='size-100'>
                        <Text UNSAFE_className={classes.selectedRow}>Selected: {selectedFile.name}</Text>
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
