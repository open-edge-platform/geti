// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { ViewModes } from '@shared/components/media-view-modes/utils';
import { act, fireEvent, screen, waitFor, waitForElementToBeRemoved, within } from '@testing-library/react';

import { DOMAIN } from '../../../../core/projects/core.interface';
import { createInMemoryProjectService } from '../../../../core/projects/services/in-memory-project-service';
import { Task } from '../../../../core/projects/task.interface';
import { getMockedScreenshot } from '../../../../test-utils/mocked-items-factory/mocked-camera';
import { getMockedProjectIdentifier } from '../../../../test-utils/mocked-items-factory/mocked-identifiers';
import { getMockedLabel } from '../../../../test-utils/mocked-items-factory/mocked-labels';
import { getMockedProject } from '../../../../test-utils/mocked-items-factory/mocked-project';
import { getMockedTask } from '../../../../test-utils/mocked-items-factory/mocked-tasks';
import { providersRender as render } from '../../../../test-utils/required-providers-render';
import { TaskProvider } from '../../../annotator/providers/task-provider/task-provider.component';
import { Screenshot, UserCameraPermission } from '../../../camera-support/camera.interface';
import { ProjectProvider } from '../../../project-details/providers/project-provider/project-provider.component';
import { useCameraParams } from '../../hooks/camera-params.hook';
import { getUseCameraParams } from '../../test-utils/camera-params';
import { configUseCamera, configUseCameraStorage } from '../../test-utils/config-use-camera';
import { MediaItemsList } from './media-items-list.component';

jest.mock('../../../camera-support/use-camera.hook');

jest.mock('../../hooks/camera-params.hook', () => ({
    ...jest.requireActual('../../hooks/camera-params.hook'),
    useCameraParams: jest.fn(),
}));

const screenShotId = 'image-id-test';
const mockedScreenshot = getMockedScreenshot({ id: screenShotId });

const renderApp = async ({
    filesData = [],
    mockedSaveMedia = jest.fn(),
    mockedUpdateMany = jest.fn(),
    tasks = [getMockedTask({ domain: DOMAIN.DETECTION, labels: [] })],
}: {
    tasks?: Task[];
    mockedSaveMedia?: jest.Mock;
    mockedUpdateMany?: jest.Mock;
    filesData: Screenshot[];
}) => {
    configUseCamera({ userPermissions: UserCameraPermission.GRANTED });

    configUseCameraStorage({
        filesData,
        saveMedia: mockedSaveMedia,
        updateMany: mockedUpdateMany,
        deleteMany: () => Promise.resolve(),
    });

    jest.mocked(useCameraParams).mockReturnValue(getUseCameraParams());

    const projectService = createInMemoryProjectService();
    projectService.getProject = async () => getMockedProject({ tasks });

    render(
        <ProjectProvider projectIdentifier={getMockedProjectIdentifier({})}>
            <TaskProvider>
                <MediaItemsList screenshots={filesData} viewMode={ViewModes.MEDIUM} />
            </TaskProvider>
        </ProjectProvider>,
        { services: { projectService } }
    );

    await waitForElementToBeRemoved(screen.getAllByRole('progressbar'));
};

describe('MediaItemsList', () => {
    it('updates item label and invalidate query', async () => {
        const mockedUpdateMany = jest.fn();
        const mockedLabel = getMockedLabel({ name: 'camera-label-2' });

        await renderApp({
            mockedUpdateMany,
            filesData: [mockedScreenshot],
            tasks: [getMockedTask({ domain: DOMAIN.CLASSIFICATION, labels: [mockedLabel] })],
        });

        act(() => {
            fireEvent.click(screen.getByRole('button', { name: 'Unlabeled' }));
        });

        act(() => {
            const labelListContainer = screen.getByLabelText('label search results');
            fireEvent.click(within(labelListContainer).getByText(mockedLabel.name));
        });

        expect(mockedUpdateMany).toHaveBeenCalledWith(
            [mockedScreenshot.id],
            expect.objectContaining({ labelIds: [mockedLabel.id] })
        );
    });

    it('remove selected label', async () => {
        const mockedUpdateMany = jest.fn();
        const mockedLabel = getMockedLabel({ name: 'camera-label-2' });

        await renderApp({
            mockedUpdateMany,
            filesData: [{ ...mockedScreenshot, labelIds: [mockedLabel.id] }],
            tasks: [getMockedTask({ domain: DOMAIN.CLASSIFICATION, labels: [mockedLabel] })],
        });

        act(() => {
            fireEvent.click(screen.getByRole('button', { name: mockedLabel.name }));
        });

        act(() => {
            const labelListContainer = screen.getByLabelText('label search results');
            fireEvent.click(within(labelListContainer).getByText(mockedLabel.name));
        });

        expect(mockedUpdateMany).toHaveBeenCalledWith(
            [mockedScreenshot.id],
            expect.objectContaining({ labelIds: [], labelName: null })
        );
    });

    it('open preview modal and close it after deleting media', async () => {
        const mockedLabel = getMockedLabel({ name: 'camera-label-2' });

        await renderApp({
            filesData: [mockedScreenshot],
            tasks: [getMockedTask({ domain: DOMAIN.CLASSIFICATION, labels: [mockedLabel] })],
        });

        fireEvent.click(screen.getByRole('img', { name: `media item ${screenShotId}` }));

        const previewImage = screen.getByRole('img', { name: `full screen screenshot ${screenShotId}` });

        const container = previewImage?.parentElement as HTMLElement;
        expect(previewImage).toBeVisible();

        fireEvent.click(within(container).getByRole('button', { name: /delete/i }));

        const confirmationContainer = screen.getByText(/^are you sure you want to delete this photo/i)
            .parentElement as HTMLElement;

        fireEvent.click(within(confirmationContainer).getByRole('button', { name: /delete/i }));

        await waitFor(() => {
            expect(
                screen.queryByRole('img', { name: `full screen screenshot ${screenShotId}` })
            ).not.toBeInTheDocument();
        });
    });
});
