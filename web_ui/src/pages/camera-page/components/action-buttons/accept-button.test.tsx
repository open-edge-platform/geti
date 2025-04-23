// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { fireEvent, screen, waitFor } from '@testing-library/react';

import { MediaUploadProvider } from '../../../../providers/media-upload-provider/media-upload-provider.component';
import { getMockedScreenshot } from '../../../../test-utils/mocked-items-factory/mocked-camera';
import { getMockedDatasetIdentifier } from '../../../../test-utils/mocked-items-factory/mocked-identifiers';
import { providersRender as render } from '../../../../test-utils/required-providers-render';
import { Screenshot } from '../../../camera-support/camera.interface';
import { ProjectProvider } from '../../../project-details/providers/project-provider/project-provider.component';
import { useCameraParams } from '../../hooks/camera-params.hook';
import { getUseCameraParams } from '../../test-utils/camera-params';
import { configUseCameraStorage } from '../../test-utils/config-use-camera';
import { AcceptButton } from './accept-button.component';

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

describe('AcceptButton', () => {
    const renderApp = async ({
        filesData,
        isLivePrediction = false,
        updateMany = jest.fn().mockResolvedValue(''),
        deleteAllItems = jest.fn().mockResolvedValue(''),
        onPress = undefined,
    }: {
        onPress?: () => void;
        filesData?: Screenshot[];
        isLivePrediction?: boolean;
        updateMany?: jest.Mock;
        deleteAllItems?: jest.Mock;
        mockedGetBrowserPermissions?: jest.Mock;
    }) => {
        jest.mocked(useCameraParams).mockReturnValue(
            getUseCameraParams({ isLivePrediction, ...mockedDatasetIdentifier })
        );

        configUseCameraStorage({ deleteAllItems, updateMany, filesData });

        render(
            <ProjectProvider
                projectIdentifier={{
                    projectId: 'project-id',
                    workspaceId: 'workspace-id',
                    organizationId: 'organization-id',
                }}
            >
                <MediaUploadProvider>
                    <AcceptButton onPress={onPress} />
                </MediaUploadProvider>
            </ProjectProvider>
        );
    };

    beforeEach(() => {
        jest.clearAllMocks();
    });

    const filesData = [mockedScreenshot];

    it('livePrediction is true', async () => {
        const mockedUpdateMany = jest.fn().mockResolvedValue('');
        await renderApp({ isLivePrediction: true, updateMany: mockedUpdateMany, filesData });

        await waitFor(() => {
            fireEvent.click(screen.getByRole('button', { name: /accept/i }));
        });

        expect(mockedNavigate).toHaveBeenCalledWith(expect.stringContaining('/tests/live-prediction'));
        expect(mockedUpdateMany).toHaveBeenCalledWith([mockedScreenshot.id], { isAccepted: true });
    });

    it('livePrediction is false and custom onPress function is passed', async () => {
        const mockedUpdateMany = jest.fn().mockResolvedValue('');
        const mockedOnPress = jest.fn();
        await renderApp({ isLivePrediction: false, updateMany: mockedUpdateMany, filesData, onPress: mockedOnPress });

        await waitFor(() => {
            fireEvent.click(screen.getByRole('button', { name: /accept/i }));
        });

        expect(mockedUpdateMany).toHaveBeenCalledWith([mockedScreenshot.id], { isAccepted: true });
        expect(mockedOnPress).toHaveBeenCalled();
        expect(mockedNavigate).toHaveBeenCalledWith(
            `/organizations/${mockedDatasetIdentifier.organizationId}/workspaces/${mockedDatasetIdentifier.workspaceId}/projects/${mockedDatasetIdentifier.projectId}/datasets/${mockedDatasetIdentifier.datasetId}`
        );
        expect(mockedOnPress.mock.invocationCallOrder[0]).toBeLessThan(mockedNavigate.mock.invocationCallOrder[0]);
    });

    it('empty data', async () => {
        const mockedUpdateMany = jest.fn().mockResolvedValue('');
        await renderApp({ updateMany: mockedUpdateMany, filesData: undefined });

        await waitFor(() => {
            fireEvent.click(screen.getByRole('button', { name: /accept/i }));
        });

        expect(mockedUpdateMany).toHaveBeenCalledWith([], { isAccepted: true });
    });
});
