// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { fireEvent, screen, waitFor, within } from '@testing-library/react';

import { MediaUploadProvider } from '../../../../providers/media-upload-provider/media-upload-provider.component';
import { getMockedScreenshot } from '../../../../test-utils/mocked-items-factory/mocked-camera';
import { getMockedDatasetIdentifier } from '../../../../test-utils/mocked-items-factory/mocked-identifiers';
import { providersRender as render } from '../../../../test-utils/required-providers-render';
import { Screenshot } from '../../../camera-support/camera.interface';
import { ProjectProvider } from '../../../project-details/providers/project-provider/project-provider.component';
import { useCameraParams } from '../../hooks/camera-params.hook';
import { getUseCameraParams } from '../../test-utils/camera-params';
import { configUseCameraStorage } from '../../test-utils/config-use-camera';
import { ActionButtons } from './action-buttons.component';

const mockedNavigate = jest.fn();
jest.mock('react-router-dom', () => ({
    ...jest.requireActual('react-router-dom'),
    useNavigate: () => mockedNavigate,
}));

jest.mock('../../hooks/camera-params.hook', () => ({
    ...jest.requireActual('../../hooks/camera-params.hook'),
    useCameraParams: jest.fn(),
}));

const mockedDatasetIdentifier = getMockedDatasetIdentifier();

const mockedScreenshot = getMockedScreenshot({});

describe('ActionButtons', () => {
    const renderApp = async ({
        canGoToCameraPage = false,
        isLivePrediction = false,
        filesData = [mockedScreenshot],
        deleteAllItems = jest.fn().mockResolvedValue(''),
    }: {
        filesData?: Screenshot[];
        canGoToCameraPage?: boolean;
        isLivePrediction?: boolean;
        deleteAllItems?: jest.Mock;
        mockedGetBrowserPermissions?: jest.Mock;
    }) => {
        jest.mocked(useCameraParams).mockReturnValue(
            getUseCameraParams({ isLivePrediction, ...mockedDatasetIdentifier })
        );

        configUseCameraStorage({ deleteAllItems, filesData });

        render(
            <ProjectProvider
                projectIdentifier={{
                    projectId: 'project-id',
                    workspaceId: 'workspace-id',
                    organizationId: 'organization-id',
                }}
            >
                <MediaUploadProvider>
                    <ActionButtons isDisabled={false} canGoToCameraPage={canGoToCameraPage} />
                </MediaUploadProvider>
            </ProjectProvider>
        );
    };

    beforeEach(() => {
        jest.clearAllMocks();
    });

    it('savedFilesQuery is empty, buttons are disabled', async () => {
        await renderApp({ isLivePrediction: true, filesData: [] });

        await waitFor(() => {
            expect(screen.getByRole('button', { name: /cancel/i })).toBeEnabled();
            expect(screen.getByRole('button', { name: /accept/i })).toBeDisabled();
        });
    });

    it('"take shots" redirects to "camera" page', async () => {
        await renderApp({ isLivePrediction: true, canGoToCameraPage: true });

        await waitFor(() => {
            fireEvent.click(screen.getByRole('button', { name: /take shots/i }));
        });

        expect(mockedNavigate).toHaveBeenCalledWith(expect.stringContaining('/camera'));
    });

    it('"discard all" calls deleteAllItems', async () => {
        const mockedDeleteAllItems = jest.fn().mockResolvedValue('');
        await renderApp({ isLivePrediction: false, deleteAllItems: mockedDeleteAllItems });

        await waitFor(() => {
            fireEvent.click(screen.getByRole('button', { name: /discard all/i }));
        });

        const alertdialog = screen.getByRole('alertdialog');
        fireEvent.click(within(alertdialog).getByRole('button', { name: /discard all/i }));

        await waitFor(() => {
            expect(mockedNavigate).not.toHaveBeenCalled();
            expect(mockedDeleteAllItems).toHaveBeenCalled();
        });
    });

    describe('cancel button', () => {
        it('live prediction mode on, redirects to "tests/live-prediction"', async () => {
            const mockedDeleteAllItems = jest.fn().mockResolvedValue('');
            await renderApp({ isLivePrediction: true, deleteAllItems: mockedDeleteAllItems });

            await waitFor(() => {
                fireEvent.click(screen.getByRole('button', { name: /cancel/i }));
            });

            expect(mockedDeleteAllItems).toHaveBeenCalled();
            expect(mockedNavigate).toHaveBeenCalledWith(expect.stringContaining('/tests/live-prediction'));
        });

        it('live prediction mode off, redirects to dataset page', async () => {
            const mockedDeleteAllItems = jest.fn().mockResolvedValue('');
            await renderApp({ isLivePrediction: false, filesData: [], deleteAllItems: mockedDeleteAllItems });

            await waitFor(() => {
                fireEvent.click(screen.getByRole('button', { name: /cancel/i }));
            });

            expect(mockedDeleteAllItems).not.toHaveBeenCalled();
            expect(mockedNavigate).toHaveBeenCalledWith(
                `/organizations/${mockedDatasetIdentifier.organizationId}/workspaces/${mockedDatasetIdentifier.workspaceId}/projects/${mockedDatasetIdentifier.projectId}/datasets/${mockedDatasetIdentifier.datasetId}`
            );
        });
    });
});
