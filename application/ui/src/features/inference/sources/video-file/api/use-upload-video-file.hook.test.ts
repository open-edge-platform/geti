// Copyright (C) 2026 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

import { uploadSourceVideo } from '@/api';
import * as actualApi from '@/api' with { rstest: 'importActual' };
import { act, waitFor } from '@testing-library/react';
import { renderHook } from 'test-utils/render';

import { useUploadVideoFile } from './use-upload-video-file.hook';

rs.mock('@/api', () => ({
    ...actualApi,
    uploadSourceVideo: rs.fn(),
}));

const file = new File(['fake-video-bytes'], 'sample.mp4', { type: 'video/mp4' });
const mediaId = '712750b2-5a82-47ee-8fba-f3dc96cb615d';

describe('useUploadVideoFile', () => {
    it('exposes the transfer progress while uploading and resets it afterwards', async () => {
        let finish: (() => void) | undefined;
        rs.mocked(uploadSourceVideo).mockImplementation(
            async (_file, options) =>
                new Promise((resolve) => {
                    options?.onProgress?.(4);
                    finish = () => resolve({ video_path: '/data/sample.mp4' });
                })
        );
        const { result } = renderHook(() => useUploadVideoFile());
        let pending: Promise<unknown> | undefined;

        act(() => {
            pending = result.current.mutateAsync(file);
        });
        await waitFor(() => expect(result.current.progress).toEqual({ bytesSent: 4, bytesTotal: 16 }));

        await act(async () => {
            finish?.();
            await pending;
        });

        expect(result.current.progress).toBeNull();
    });

    it.each([
        ['posix path', `/data/source_media/${mediaId}/sample.mp4`],
        ['Windows path', `C:\\data\\source_media\\${mediaId}\\sample.mp4`],
    ])('resolves with the video path and the media id parsed from a %s', async (_label, videoPath) => {
        rs.mocked(uploadSourceVideo).mockResolvedValue({ video_path: videoPath });
        const { result } = renderHook(() => useUploadVideoFile());

        await act(async () => {
            await expect(result.current.mutateAsync(file)).resolves.toEqual({ videoPath, mediaId });
        });
    });

    it('aborts the transfer when cancelled', async () => {
        let signal: AbortSignal | undefined;

        rs.mocked(uploadSourceVideo).mockImplementation(
            async (_file, options) =>
                new Promise((_resolve, reject) => {
                    signal = options?.signal;
                    options?.onProgress?.(1);
                    options?.signal?.addEventListener('abort', () =>
                        reject(new DOMException('The upload was cancelled.', 'AbortError'))
                    );
                })
        );
        const { result } = renderHook(() => useUploadVideoFile());
        let pending: Promise<unknown> | undefined;

        act(() => {
            pending = result.current.mutateAsync(file);
        });
        await waitFor(() => expect(result.current.progress).not.toBeNull());

        await act(async () => {
            result.current.cancel();
            await expect(pending).rejects.toMatchObject({ name: 'AbortError' });
        });

        expect(signal?.aborted).toBe(true);
        expect(result.current.progress).toBeNull();
    });

    it('aborts the transfer when unmounted', async () => {
        let signal: AbortSignal | undefined;
        rs.mocked(uploadSourceVideo).mockImplementation(
            async (_file, options) =>
                new Promise(() => {
                    signal = options?.signal;
                })
        );
        const { result, unmount } = renderHook(() => useUploadVideoFile());

        act(() => {
            void result.current.mutateAsync(file);
        });
        await waitFor(() => expect(signal).toBeDefined());

        unmount();

        expect(signal?.aborted).toBe(true);
    });

    it('rejects when the upload fails', async () => {
        rs.mocked(uploadSourceVideo).mockRejectedValue(new Error('Unsupported video format'));
        const { result } = renderHook(() => useUploadVideoFile());

        await act(async () => {
            await expect(result.current.mutateAsync(file)).rejects.toThrow('Unsupported video format');
        });
    });
});
