// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { waitFor } from '@testing-library/react';

import { MediaUploadPerDataset } from '../../../../providers/media-upload-provider/media-upload.interface';
import { getMockedScreenshot } from '../../../../test-utils/mocked-items-factory/mocked-camera';
import {
    getMockedSuccessListItem,
    mockedMediaUploadPerDataset,
} from '../../../../test-utils/mocked-items-factory/mocked-upload-items';
import { providersRender as render } from '../../../../test-utils/required-providers-render';
import { Screenshot } from '../../../camera-support/camera.interface';
import { configUseCameraStorage } from '../../test-utils/config-use-camera';
import { DatasetLoaderManager } from './dataset-loader-manager.component';

interface RenderAppProps extends Partial<MediaUploadPerDataset> {
    deleteMany?: jest.Mock;
    onFileLoaded?: jest.Mock;
    filesData?: Screenshot[];
}

describe('DatasetLoaderManager', () => {
    const renderApp = async ({ filesData, deleteMany = jest.fn(), ...datasetLoaderManager }: RenderAppProps) => {
        configUseCameraStorage({ deleteMany, filesData });

        render(<DatasetLoaderManager mediaUploadState={{ ...mockedMediaUploadPerDataset, ...datasetLoaderManager }} />);
    };

    beforeEach(() => {
        jest.clearAllMocks();
    });

    describe('deleteMany', () => {
        const mockedDeleteMany = jest.fn();
        const mockedFileName = 'file-name-test';
        const successList = [getMockedSuccessListItem(mockedFileName)];
        const mockedScreenshot = getMockedScreenshot({ fileName: mockedFileName, isAccepted: true });

        it('if loading is in progress do not delete elements', async () => {
            await renderApp({
                successList,
                isUploadInProgress: true,
                filesData: [mockedScreenshot],
                deleteMany: mockedDeleteMany,
            });

            await waitFor(() => {
                expect(mockedDeleteMany).not.toHaveBeenCalled();
            });
        });

        it('upload is in progress', async () => {
            await renderApp({
                successList,
                isUploadInProgress: false,
                filesData: [mockedScreenshot],
                deleteMany: mockedDeleteMany,
            });

            await waitFor(() => {
                expect(mockedDeleteMany).toHaveBeenCalledWith([mockedScreenshot.id]);
            });
        });
    });
});
