// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { screen, waitForElementToBeRemoved } from '@testing-library/react';

import { MediaUploadProvider } from '../../../providers/media-upload-provider/media-upload-provider.component';
import { getMockedScreenshot } from '../../../test-utils/mocked-items-factory/mocked-camera';
import { getMockedProjectIdentifier } from '../../../test-utils/mocked-items-factory/mocked-identifiers';
import { providersRender as render } from '../../../test-utils/required-providers-render';
import { TaskProvider } from '../../annotator/providers/task-provider/task-provider.component';
import { Screenshot, UserCameraPermission } from '../../camera-support/camera.interface';
import { ProjectProvider } from '../../project-details/providers/project-provider/project-provider.component';
import { useCameraParams } from '../hooks/camera-params.hook';
import { getUseCameraParams } from '../test-utils/camera-params';
import { configUseCamera, configUseCameraStorage } from '../test-utils/config-use-camera';
import { MediaGallery } from './media-gallery.component';

jest.mock('../../camera-support/use-camera.hook');

const mockedNavigate = jest.fn();
jest.mock('react-router-dom', () => ({
    ...jest.requireActual('react-router-dom'),
    useNavigate: () => mockedNavigate,
}));

jest.mock('../hooks/camera-params.hook', () => ({
    ...jest.requireActual('../hooks/camera-params.hook'),
    useCameraParams: jest.fn(),
}));

const mockedScreenshot = getMockedScreenshot({});

const renderApp = async ({ filesData }: { filesData?: Screenshot[] }) => {
    configUseCamera({ userPermissions: UserCameraPermission.GRANTED });

    configUseCameraStorage({ filesData });

    jest.mocked(useCameraParams).mockReturnValue(getUseCameraParams());

    render(
        <ProjectProvider projectIdentifier={getMockedProjectIdentifier({})}>
            <TaskProvider>
                <MediaUploadProvider>
                    <MediaGallery />
                </MediaUploadProvider>
            </TaskProvider>
        </ProjectProvider>
    );

    await waitForElementToBeRemoved(screen.getAllByRole('progressbar'));
};

describe('MediaGallery', () => {
    beforeEach(() => {
        jest.clearAllMocks();
    });

    it('empty files, redirect to camera page', async () => {
        await renderApp({ filesData: undefined });

        expect(mockedNavigate).toHaveBeenCalled();
    });

    it('render item elements', async () => {
        const filesData = [
            { ...mockedScreenshot, id: 'id-1' },
            { ...mockedScreenshot, id: 'id-2' },
        ];
        await renderApp({ filesData });

        expect(screen.queryByText('No media items')).not.toBeInTheDocument();
        expect(screen.getAllByRole('button', { name: /delete/i })).toHaveLength(filesData.length);
    });
});
