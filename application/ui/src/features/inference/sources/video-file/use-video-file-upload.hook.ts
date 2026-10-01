// Copyright (C) 2026 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

import { useRef, useState } from 'react';

import { prepareVideoFileFormData } from './utils';

export type VideoFileUploadProgress = { bytesSent: number; bytesTotal: number };

export type VideoFileUpload = {
    /** Progress of the ongoing video transfer, or `null` when no transfer is running. */
    progress: VideoFileUploadProgress | null;
    prepareFormData: (formData: FormData) => Promise<void>;
    /** Cancels the ongoing transfer; the source is then not saved. */
    cancel: () => void;
};

export const useVideoFileUpload = (): VideoFileUpload => {
    const [progress, setProgress] = useState<VideoFileUploadProgress | null>(null);
    const abortControllerRef = useRef<AbortController | null>(null);

    const prepareFormData = async (formData: FormData): Promise<void> => {
        const abortController = new AbortController();
        abortControllerRef.current = abortController;

        try {
            await prepareVideoFileFormData(formData, {
                signal: abortController.signal,
                onProgress: (bytesSent, bytesTotal) => setProgress({ bytesSent, bytesTotal }),
            });
        } finally {
            abortControllerRef.current = null;
            setProgress(null);
        }
    };

    return {
        progress,
        prepareFormData,
        cancel: () => abortControllerRef.current?.abort(),
    };
};
