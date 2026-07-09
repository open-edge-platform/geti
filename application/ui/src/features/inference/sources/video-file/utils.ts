// Copyright (C) 2025 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

import { fetchClient } from '../../../../api/client';
import type { VideoFileSourceConfig } from '../../../../api/shared-types';
import { getUniqueName } from '../utils';

export const getVideoFileInitialConfig = (existingNames: string[] = []): VideoFileSourceConfig => ({
    id: '',
    name: getUniqueName('Video file source', existingNames),
    source_type: 'video_file',
    video_path: '',
    loop: false,
});

const uploadVideoFile = async (file: File): Promise<string> => {
    const body = new FormData();
    body.append('file', file);

    const { data, error } = await fetchClient.POST('/api/sources/media', {
        // @ts-expect-error There is an incorrect type in OpenAPI
        body,
    });

    if (error !== undefined || data === undefined) {
        throw error ?? new Error('Video upload failed');
    }

    return data.video_path;
};

// Uploads the selected file (if any) and writes the resulting path back into `video_path`, so
// `videoFileBodyFormatter` can stay a plain, synchronous formatter like its sibling sources.
export const prepareVideoFileFormData = async (formData: FormData): Promise<void> => {
    const file = formData.get('video_file');

    // An untouched file input still yields a File entry (empty filename) once it has a `name`,
    // so only treat it as "a file was selected" when it actually has a name.
    if (file instanceof File && file.name !== '') {
        formData.set('video_path', await uploadVideoFile(file));
    }
};

export const videoFileBodyFormatter = (formData: FormData): VideoFileSourceConfig => ({
    id: String(formData.get('id')),
    name: String(formData.get('name')),
    source_type: 'video_file',
    video_path: String(formData.get('video_path')),
    loop: formData.get('loop') === 'on' ? true : false,
});
