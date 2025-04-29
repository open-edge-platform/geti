// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { fireEvent, screen } from '@testing-library/react';

import { MediaUploadPerDataset } from '../../../../../providers/media-upload-provider/media-upload.interface';
import {
    getMockedErrorListItem,
    getMockedSuccessListItem,
    mockedListItem,
    mockedMediaUploadPerDataset,
} from '../../../../../test-utils/mocked-items-factory/mocked-upload-items';
import { projectRender } from '../../../../../test-utils/project-provider-render';
import { UploadStatusBar } from './upload-status-bar.component';

jest.mock('../../project-dataset/hooks/dataset-media-upload', () => ({
    useDatasetMediaUpload: jest.fn(() => ({
        reset: jest.fn(),
        mediaUploadState: mockedMediaUploadPerDataset,
    })),
}));
const render = async ({
    reset = jest.fn(),
    mediaUploadState,
}: {
    reset?: () => void;
    mediaUploadState: MediaUploadPerDataset;
}) => {
    return projectRender(
        <UploadStatusBar
            reset={reset}
            onUploadMedia={jest.fn()}
            abortMediaUploads={jest.fn()}
            mediaUploadState={mediaUploadState}
        />
    );
};

const openAndCloseUploadStatusDialog = (heading: string) => {
    fireEvent.click(screen.getByRole('button', { name: /details/i }));
    expect(screen.getByRole('heading', { name: heading })).toBeVisible();

    fireEvent.click(screen.getByRole('button', { name: /hide/i }));
    expect(screen.queryByRole('heading', { name: heading })).not.toBeInTheDocument();
};

describe('UploadStatusBar', () => {
    const mockedFileName = 'file-name-test';
    const waitingQueue = [mockedListItem(mockedFileName)];
    const errorList = [getMockedErrorListItem(mockedFileName)];
    const successList = [getMockedSuccessListItem(mockedFileName)];

    beforeEach(() => {
        jest.clearAllMocks();
    });

    it('loading progress bar is visible', async () => {
        await render({
            mediaUploadState: {
                ...mockedMediaUploadPerDataset,
                waitingQueue,
                isUploadInProgress: true,
                isUploadStatusBarVisible: true,
            },
        });

        openAndCloseUploadStatusDialog('Uploading');
        expect(screen.getByRole('progressbar')).toBeVisible();
        expect(screen.getByText('1 file left')).toBeVisible();
        expect(screen.getByText('Upload pending...')).toBeVisible();
        expect(screen.queryByRole('button', { name: /close notification/i })).not.toBeInTheDocument();
    });

    describe('loaded items bar is visible', () => {
        it('all items succeed', async () => {
            const mockedReset = jest.fn();

            await render({
                reset: mockedReset,
                mediaUploadState: {
                    ...mockedMediaUploadPerDataset,
                    successList,
                    isUploadInProgress: false,
                    isUploadStatusBarVisible: true,
                },
            });

            openAndCloseUploadStatusDialog('Uploaded');
            expect(screen.getByText('Uploaded 1 of 1 file')).toBeVisible();

            fireEvent.click(screen.getByRole('button', { name: /close notification/i }));
            expect(mockedReset).toHaveBeenCalled();
        });

        it('some items failed', async () => {
            await render({
                mediaUploadState: {
                    ...mockedMediaUploadPerDataset,
                    errorList,
                    successList,
                    isUploadInProgress: false,
                    isUploadStatusBarVisible: true,
                },
            });

            openAndCloseUploadStatusDialog('Uploaded');
            expect(screen.getByText('Uploaded 1 of 2 files - 1 error')).toBeVisible();
        });
    });
});
