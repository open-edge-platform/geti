// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { act, fireEvent, screen, waitFor, waitForElementToBeRemoved, within } from '@testing-library/react';

import { DOMAIN } from '../../../core/projects/core.interface';
import { createInMemoryProjectService } from '../../../core/projects/services/in-memory-project-service';
import { Task } from '../../../core/projects/task.interface';
import { getMockedProjectIdentifier } from '../../../test-utils/mocked-items-factory/mocked-identifiers';
import { getMockedLabel } from '../../../test-utils/mocked-items-factory/mocked-labels';
import { getMockedProject } from '../../../test-utils/mocked-items-factory/mocked-project';
import { getMockedTask } from '../../../test-utils/mocked-items-factory/mocked-tasks';
import { providersRender as render } from '../../../test-utils/required-providers-render';
import { TaskProvider } from '../../annotator/providers/task-provider/task-provider.component';
import { UserCameraPermission } from '../../camera-support/camera.interface';
import { ProjectProvider } from '../../project-details/providers/project-provider/project-provider.component';
import { useCameraParams } from '../hooks/camera-params.hook';
import { DeviceSettingsProvider } from '../providers/device-settings-provider.component';
import { getUseCameraParams } from '../test-utils/camera-params';
import { configUseCamera, configUseCameraStorage } from '../test-utils/config-use-camera';
import { CameraFactory } from './camera-factory.component';

jest.mock('../../camera-support/use-camera.hook');

// This component has animation-transitions that influence the 'onPress' handler,
// that case have been tested on its tests file and hence isn't worth re-doing it here
jest.mock('./action-buttons/capture-button-animation.component', () => ({
    CaptureButtonAnimation: (props: { onPress: () => void }) => <button onClick={props.onPress}>capture photo</button>,
}));

jest.mock('../../../shared/navigator-utils', () => ({
    ...jest.requireActual('../../../shared/navigator-utils'),
    getVideoDevices: jest.fn().mockResolvedValue([]),
}));

jest.mock('../hooks/camera-params.hook', () => ({
    ...jest.requireActual('../hooks/camera-params.hook'),
    useCameraParams: jest.fn(),
}));

const renderApp = async ({
    defaultLabelId = '',
    hasDefaultLabel = false,
    isPermissionDenied = false,
    isPermissionPending = false,
    mockedSaveMedia = jest.fn(),
    tasks = [getMockedTask({ domain: DOMAIN.DETECTION, labels: [] })],
}: {
    tasks?: Task[];
    defaultLabelId?: string;
    hasDefaultLabel?: boolean;
    isPermissionDenied?: boolean;
    isPermissionPending?: boolean;
    mockedSaveMedia?: jest.Mock;
}) => {
    configUseCamera({ userPermissions: UserCameraPermission.GRANTED });

    jest.mocked(useCameraParams).mockReturnValue(getUseCameraParams({ defaultLabelId, hasDefaultLabel }));

    configUseCameraStorage({ saveMedia: mockedSaveMedia });

    const projectService = createInMemoryProjectService();
    projectService.getProject = async () => getMockedProject({ tasks });

    render(
        <ProjectProvider projectIdentifier={getMockedProjectIdentifier({})}>
            <TaskProvider>
                <DeviceSettingsProvider>
                    <CameraFactory isPermissionDenied={isPermissionDenied} isPermissionPending={isPermissionPending} />
                </DeviceSettingsProvider>
            </TaskProvider>
        </ProjectProvider>,
        {
            services: { projectService },
        }
    );

    await waitForElementToBeRemoved(screen.getAllByRole('progressbar'));
};

describe('CameraFactory', () => {
    const selectLabel = (labelName: string, triggerName: string | RegExp = /Select label/i) => {
        fireEvent.click(screen.getByRole('button', { name: triggerName }));

        const labelListContainer = screen.getByLabelText('label search results');
        fireEvent.click(within(labelListContainer).getByText(labelName));
    };

    it('permission pending', async () => {
        await renderApp({ isPermissionPending: true });

        expect(screen.getByLabelText(/permissions pending/i)).toBeVisible();
    });

    it('permission denied', async () => {
        await renderApp({ isPermissionDenied: true });

        expect(screen.getAllByText(/camera connection is lost/i)).toHaveLength(2);
    });

    describe('label selector is visible', () => {
        it.each([
            DOMAIN.CLASSIFICATION,
            DOMAIN.ANOMALY_CLASSIFICATION,
            DOMAIN.ANOMALY_DETECTION,
            DOMAIN.ANOMALY_SEGMENTATION,
        ])('task type: %o', async (taskType) => {
            await renderApp({ tasks: [getMockedTask({ domain: taskType, labels: [] })] });

            expect(screen.getByRole('button', { name: /Select label/i })).toBeVisible();
        });
    });

    describe('label selector', () => {
        const mockedSaveMedia = jest.fn();

        it('hidden for task-chain projects, take a picture with empty ids', async () => {
            const mockedLabel = getMockedLabel({ name: 'camera-label-2' });

            await renderApp({
                mockedSaveMedia,
                tasks: [
                    getMockedTask({ domain: DOMAIN.DETECTION, labels: [mockedLabel] }),
                    getMockedTask({ domain: DOMAIN.CLASSIFICATION, labels: [mockedLabel] }),
                ],
            });

            fireEvent.click(screen.getByRole('button', { name: /capture photo/i }));

            expect(screen.queryByRole('button', { name: /Select label/i })).not.toBeInTheDocument();

            await waitFor(() => {
                expect(mockedSaveMedia).toHaveBeenCalledWith({
                    id: expect.any(String),
                    dataUrl: null,
                    labelIds: [],
                    labelName: null,
                });
            });
        });

        it('visible, take a picture with ids', async () => {
            const mockedLabel = getMockedLabel({ name: 'camera-label-2' });

            await renderApp({
                mockedSaveMedia,
                tasks: [getMockedTask({ domain: DOMAIN.CLASSIFICATION, labels: [mockedLabel] })],
            });

            selectLabel(mockedLabel.name);

            fireEvent.click(screen.getByRole('button', { name: /capture photo/i }));

            await waitFor(() => {
                expect(mockedSaveMedia).toHaveBeenCalledWith({
                    id: expect.any(String),
                    labelIds: [mockedLabel.id],
                    labelName: mockedLabel.name,
                    dataUrl: null,
                });
            });
        });

        it('toggle label selection', async () => {
            const mockedLabel = getMockedLabel({ name: 'camera-label-1' });

            await renderApp({
                tasks: [getMockedTask({ domain: DOMAIN.CLASSIFICATION, labels: [mockedLabel] })],
            });

            selectLabel(mockedLabel.name);

            expect(screen.getByRole('button', { name: mockedLabel.name })).toBeVisible();
            expect(screen.queryByRole('button', { name: /Select label/i })).not.toBeInTheDocument();

            selectLabel(mockedLabel.name, mockedLabel.name);

            expect(screen.getByRole('button', { name: /Select label/i })).toBeVisible();
            expect(screen.queryByRole('button', { name: mockedLabel.name })).not.toBeInTheDocument();
        });

        it('for anomaly projects the user needs to choose either "normal" or "anomalous" label', async () => {
            const mockedLabelOne = getMockedLabel({ name: 'camera-label-one', id: '1' });
            const mockedLabelTwo = getMockedLabel({ name: 'camera-label-two', id: '2' });

            await renderApp({
                hasDefaultLabel: true,
                defaultLabelId: mockedLabelOne.id,
                tasks: [getMockedTask({ domain: DOMAIN.ANOMALY_DETECTION, labels: [mockedLabelOne, mockedLabelTwo] })],
            });

            selectLabel(mockedLabelOne.name, mockedLabelOne.name);

            expect(screen.getByRole('button', { name: mockedLabelOne.name })).toBeVisible();
            expect(screen.queryByRole('button', { name: /Select label/i })).not.toBeInTheDocument();

            selectLabel(mockedLabelTwo.name, mockedLabelOne.name);

            expect(screen.getByRole('button', { name: mockedLabelTwo.name })).toBeVisible();
            expect(screen.queryByRole('button', { name: /Select label/i })).not.toBeInTheDocument();
        });

        it('for anomaly projects we must have always one label selected', async () => {
            const mockedLabelOne = getMockedLabel({ name: 'camera-label-one', id: '1' });

            await renderApp({
                hasDefaultLabel: true,
                defaultLabelId: '1',
                tasks: [getMockedTask({ domain: DOMAIN.ANOMALY_DETECTION, labels: [mockedLabelOne] })],
            });

            act(() => {
                expect(screen.getByRole('button', { name: mockedLabelOne.name })).toBeVisible();
            });
        });

        it('correctly selects multiple labels', async () => {
            // To mimic Multi-label classification project we need:
            // 1) Labels with different groups
            // 2) Labels without label parent id
            const mockedLabel = getMockedLabel({ name: 'camera-label-1', group: 'first-group', id: '1' });
            const mockedLabelTwo = getMockedLabel({ name: 'camera-label-2', group: 'second-group', id: '2' });
            const mockedLabelThree = getMockedLabel({ name: 'camera-label-3', group: 'third-group', id: '3' });

            await renderApp({
                tasks: [
                    getMockedTask({
                        domain: DOMAIN.CLASSIFICATION,
                        labels: [mockedLabel, mockedLabelTwo, mockedLabelThree],
                    }),
                ],
            });

            // Select 2 labels
            selectLabel(mockedLabel.name);

            expect(screen.getByRole('button', { name: mockedLabel.name })).toBeVisible();
            expect(screen.queryByRole('button', { name: /Select label/i })).not.toBeInTheDocument();

            // Select another label
            selectLabel(mockedLabelTwo.name, mockedLabel.name);

            expect(screen.getByRole('button', { name: mockedLabel.name })).toBeInTheDocument();
            expect(screen.getByRole('button', { name: mockedLabelTwo.name })).toBeInTheDocument();
        });
    });

    it('default label selected', async () => {
        const mockedLabel = getMockedLabel({ id: '123', name: 'camera-label-2' });

        await renderApp({
            hasDefaultLabel: true,
            defaultLabelId: mockedLabel.id,
            tasks: [getMockedTask({ domain: DOMAIN.ANOMALY_CLASSIFICATION, labels: [mockedLabel] })],
        });

        expect(screen.getByRole('button', { name: mockedLabel.name })).toBeVisible();
        expect(screen.getByRole('button', { name: mockedLabel.name })).toBeEnabled();
    });
});
