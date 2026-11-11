// Copyright (C) 2026 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

import { useEffect, useRef, useState } from 'react';

import { isAbortError, uploadSourceVideo } from '@/api';
import { useMutation } from '@tanstack/react-query';

export interface VideoFileUploadProgress {
    bytesSent: number;
    bytesTotal: number;
}

export interface UploadedVideoFile {
    videoPath: string;
    mediaId: string | undefined;
}

export const useUploadVideoFile = () => {
    const [progress, setProgress] = useState<VideoFileUploadProgress | null>(null);
    const abortControllerRef = useRef<AbortController | null>(null);

    const { mutateAsync, isPending } = useMutation({
        mutationFn: async (file: File): Promise<UploadedVideoFile> => {
            const abortController = new AbortController();
            abortControllerRef.current = abortController;

            try {
                const { video_path } = await uploadSourceVideo(file, {
                    signal: abortController.signal,
                    onProgress: (bytesSent) => setProgress({ bytesSent, bytesTotal: file.size }),
                });

                return { videoPath: video_path, mediaId: video_path.split(/[\\/]/).at(-2) };
            } finally {
                abortControllerRef.current = null;
                setProgress(null);
            }
        },
        meta: { error: { notify: (error: unknown) => !isAbortError(error) } },
    });

    useEffect(() => {
        return () => {
            abortControllerRef.current?.abort();
        };
    }, []);

    return {
        mutateAsync,
        isPending,
        progress,
        cancel: () => abortControllerRef.current?.abort(),
    };
};
