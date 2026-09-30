// Copyright (C) 2026 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

import { uploadDatasetMediaResumable } from '@/api';
import { act, waitFor } from '@testing-library/react';
import { getMockedMediaImage } from 'mocks/mock-media';
import { renderHook } from 'test-utils/render';
import { beforeEach, vi } from 'vitest';

import { useMediaUploadState } from '../providers/media-upload-context';
import { MediaUploadProvider } from '../providers/media-upload-provider.component';
import { computeSummary } from '../providers/media-upload-reducer';
import { MEDIA_UPLOAD_CONCURRENCY, useMediaUpload } from './use-media-upload';

vi.mock('@/api', () => ({ uploadDatasetMediaResumable: vi.fn() }));
const uploadMock = vi.mocked(uploadDatasetMediaResumable);

const useMediaUploadProgress = () => {
    const upload = useMediaUpload();
    const state = useMediaUploadState();

    return { upload, state, uploadProgress: computeSummary(state.items) };
};

const renderUpload = () => renderHook(() => useMediaUploadProgress(), { wrapper: MediaUploadProvider });
const uploadMediaAndWaitForCompletion = async (
    uploadMedia: (files: File[]) => Promise<unknown>,
    files: File[],
    isUploading: () => boolean
) => {
    await act(async () => {
        await uploadMedia(files);
    });

    await waitFor(() => {
        expect(isUploading()).toBe(false);
    });
};

describe('useMediaUpload', () => {
    beforeEach(() => {
        uploadMock.mockReset();
    });

    it('tracks transferred bytes separately from server processing', async () => {
        let finishProcessing: ((media: ReturnType<typeof getMockedMediaImage>) => void) | undefined;
        uploadMock.mockImplementation(
            async (_projectId, file, onProgress) =>
                new Promise((resolve) => {
                    onProgress?.(2);
                    onProgress?.(file.size);
                    finishProcessing = resolve;
                })
        );
        const { result } = renderUpload();
        const file = new File(['file'], 'image.jpg');
        let pending: Promise<unknown>;
        act(() => {
            pending = result.current.upload.uploadMedia([file]);
        });

        await waitFor(() =>
            expect(result.current.state.items[0]).toMatchObject({
                bytesSent: file.size,
                status: 'processing',
            })
        );
        await act(async () => {
            finishProcessing?.(getMockedMediaImage({ id: crypto.randomUUID() }));
            await pending;
        });
        expect(result.current.state.items[0].status).toBe('uploaded');
    });

    it('uploads all selected files', async () => {
        const uploadedFileNames: string[] = [];

        uploadMock.mockImplementation(async (projectId, file) => {
            uploadedFileNames.push(file.name);
            expect(projectId).toBe('123');
            return getMockedMediaImage({ id: crypto.randomUUID() });
        });

        const { result } = renderUpload();

        const files = [
            new File(['file-1'], 'image-1.jpg', { type: 'image/jpeg' }),
            new File(['file-2'], 'image-2.jpg', { type: 'image/jpeg' }),
        ];

        await uploadMediaAndWaitForCompletion(
            result.current.upload.uploadMedia,
            files,
            () => result.current.state.isUploading
        );

        expect(uploadedFileNames).toEqual(['image-1.jpg', 'image-2.jpg']);
    });

    it('does not exceed configured upload concurrency', async () => {
        let runningUploads = 0;
        let maxRunningUploads = 0;

        uploadMock.mockImplementation(async () => {
            runningUploads += 1;
            maxRunningUploads = Math.max(maxRunningUploads, runningUploads);
            await new Promise((resolve) => setTimeout(resolve, 20));
            runningUploads -= 1;
            return getMockedMediaImage({ id: crypto.randomUUID() });
        });

        const { result } = renderUpload();

        const mockFiles = Array.from(
            { length: 12 },
            (_, index) => new File([`file-${index}`], `image-${index}.jpg`, { type: 'image/jpeg' })
        );

        await uploadMediaAndWaitForCompletion(
            result.current.upload.uploadMedia,
            mockFiles,
            () => result.current.state.isUploading
        );

        expect(maxRunningUploads).toBeLessThanOrEqual(MEDIA_UPLOAD_CONCURRENCY);
        expect(result.current.uploadProgress.succeeded).toBe(12);
    });

    it('tracks upload progress counters', async () => {
        let requestCount = 0;

        uploadMock.mockImplementation(async () => {
            requestCount += 1;
            if (requestCount === 2) {
                throw new Error('Upload failed');
            }
            return getMockedMediaImage({ id: crypto.randomUUID() });
        });

        const { result } = renderUpload();

        const files = [
            new File(['ok-file'], 'ok.jpg', { type: 'image/jpeg' }),
            new File(['broken-file'], 'broken.jpg', { type: 'image/jpeg' }),
        ];

        await uploadMediaAndWaitForCompletion(
            result.current.upload.uploadMedia,
            files,
            () => result.current.state.isUploading
        );

        expect(result.current.uploadProgress).toEqual({
            total: 2,
            succeeded: 1,
            failed: 1,
        });
    });

    it('tracks per-file status and error messages', async () => {
        uploadMock.mockImplementation(async (_projectId, file) => {
            if (file.name === 'broken.jpg') {
                throw new Error('Upload failed');
            }
            return getMockedMediaImage({ id: crypto.randomUUID() });
        });

        const { result } = renderUpload();

        const files = [
            new File(['ok-file'], 'ok.jpg', { type: 'image/jpeg' }),
            new File(['broken-file'], 'broken.jpg', { type: 'image/jpeg' }),
        ];

        await uploadMediaAndWaitForCompletion(
            result.current.upload.uploadMedia,
            files,
            () => result.current.state.isUploading
        );

        const items = result.current.state.items;
        expect(items).toHaveLength(2);
        expect(items[0]).toMatchObject({ name: 'ok.jpg', status: 'uploaded' });
        expect(items[1]).toMatchObject({ name: 'broken.jpg', status: 'failed' });
        expect(items[1].errorMessage).toBeTruthy();
    });
});
