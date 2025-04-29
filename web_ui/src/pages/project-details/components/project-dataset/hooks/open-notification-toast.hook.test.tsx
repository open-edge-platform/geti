// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { ReactNode } from 'react';

import { renderHook, waitFor } from '@testing-library/react';

import { createInMemoryModelsService } from '../../../../../core/models/services/in-memory-models-service';
import { DOMAIN } from '../../../../../core/projects/core.interface';
import { createInMemoryProjectService } from '../../../../../core/projects/services/in-memory-project-service';
import { LifecycleStage } from '../../../../../core/supported-algorithms/dtos/supported-algorithms.interface';
import { createInMemorySupportedAlgorithmsService } from '../../../../../core/supported-algorithms/services/in-memory-supported-algorithms-service';
import { getMockedSupportedAlgorithm } from '../../../../../core/supported-algorithms/services/test-utils';
import { NOTIFICATION_TYPE } from '../../../../../notification/notification-toast/notification-type.enum';
import {
    getMockedModelsGroupAlgorithmDetails,
    getMockedModelVersion,
} from '../../../../../test-utils/mocked-items-factory/mocked-model';
import { getMockedProject } from '../../../../../test-utils/mocked-items-factory/mocked-project';
import { RequiredProviders } from '../../../../../test-utils/required-providers-render';
import { ProjectProvider } from '../../../providers/project-provider/project-provider.component';
import { useOpenNotificationToast } from './open-notification-toast.hook';

const activeModel = getMockedModelsGroupAlgorithmDetails({
    groupName: 'SSD',
    lifecycleStage: LifecycleStage.ACTIVE,
    modelVersions: [getMockedModelVersion({ isActiveModel: true })],
});

const deprecatedActiveModel = getMockedModelsGroupAlgorithmDetails({
    groupName: 'ATTS',
    lifecycleStage: LifecycleStage.DEPRECATED,
    modelVersions: [getMockedModelVersion({ isActiveModel: true })],
});

const obsoleteActiveModel = getMockedModelsGroupAlgorithmDetails({
    groupName: 'YOLOX',
    lifecycleStage: LifecycleStage.OBSOLETE,
    modelVersions: [getMockedModelVersion({ isActiveModel: true })],
});

const mockedSupportedAlgorithmsForDetection = [
    getMockedSupportedAlgorithm({
        name: 'YOLOX',
        domain: DOMAIN.DETECTION,
        modelSize: 200,
        modelTemplateId: 'detection_yolo',
        gigaflops: 1.3,
        summary: 'YOLO architecture for detection',
        isDefaultAlgorithm: true,
        lifecycleStage: LifecycleStage.OBSOLETE,
    }),
    getMockedSupportedAlgorithm({
        name: 'SSD',
        domain: DOMAIN.DETECTION,
        modelSize: 100,
        modelTemplateId: 'detection_ssd',
        gigaflops: 5.4,
        summary: 'SSD architecture for detection',
        isDefaultAlgorithm: false,
    }),
    getMockedSupportedAlgorithm({
        name: 'ATTS',
        domain: DOMAIN.DETECTION,
        modelSize: 150,
        modelTemplateId: 'detection_atts',
        gigaflops: 3,
        summary: 'ATTS architecture for detection',
        isDefaultAlgorithm: false,
        lifecycleStage: LifecycleStage.DEPRECATED,
    }),
];

const mockedSingleTaskProject = getMockedProject({
    id: 'project-id',
    tasks: [{ id: 'task-id', domain: DOMAIN.DETECTION, labels: [], title: DOMAIN.DETECTION }],
    labels: [],
    datasets: [{ id: 'dataset-id', name: 'test dataset', creationTime: '', useForTraining: true }],
});

const mockedProjectIdentifier = {
    workspaceId: 'workspace-id',
    projectId: 'project-id',
    organizationId: 'organization-id',
};

const mockedAddToastNotification = jest.fn();
jest.mock('../../../../../notification/notification.component', () => ({
    ...jest.requireActual('../../../../../notification/notification.component'),
    useNotification: jest.fn(() => ({ addToastNotification: mockedAddToastNotification })),
}));

describe('useOpenNotificationToast', () => {
    const projectService = createInMemoryProjectService();
    const supportedAlgorithmsService = createInMemorySupportedAlgorithmsService();
    const modelsService = createInMemoryModelsService();
    projectService.getProject = jest.fn(async () => mockedSingleTaskProject);
    supportedAlgorithmsService.getProjectSupportedAlgorithms = jest.fn(
        async () => mockedSupportedAlgorithmsForDetection
    );
    const wrapper = ({ children }: { children: ReactNode }) => {
        return (
            <RequiredProviders
                modelsService={modelsService}
                projectService={projectService}
                supportedAlgorithmsService={supportedAlgorithmsService}
            >
                <ProjectProvider projectIdentifier={mockedProjectIdentifier}>{children}</ProjectProvider>
            </RequiredProviders>
        );
    };

    beforeEach(() => {
        jest.clearAllMocks();
    });

    it('calls a toast with deprecated active model', async () => {
        const models = [activeModel, deprecatedActiveModel];
        modelsService.getModels = jest.fn(async () => models);

        renderHook(() => useOpenNotificationToast(), { wrapper });

        await waitFor(() => {
            expect(mockedAddToastNotification).toHaveBeenCalledWith(
                expect.objectContaining({
                    type: NOTIFICATION_TYPE.WARNING,
                    title: `Your active model “${deprecatedActiveModel.groupName}" is deprecated`,
                    actionButtons: expect.arrayContaining([expect.any(Object), expect.any(Object)]),
                })
            );
        });
    });

    it('calls a toast with obsolete active model', async () => {
        const models = [activeModel, obsoleteActiveModel];
        modelsService.getModels = jest.fn(async () => models);

        renderHook(() => useOpenNotificationToast(), { wrapper });
        await waitFor(() => {
            expect(mockedAddToastNotification).toHaveBeenCalledWith(
                expect.objectContaining({
                    type: NOTIFICATION_TYPE.ERROR,
                    title: `Your active model “${obsoleteActiveModel.groupName}" is Obsolete`,
                    actionButtons: expect.arrayContaining([expect.any(Object), expect.any(Object)]),
                })
            );
        });
    });

    it('does not call a toast when empty models', async () => {
        modelsService.getModels = jest.fn(async () => []);

        renderHook(() => useOpenNotificationToast(), { wrapper });

        await waitFor(() => {
            expect(mockedAddToastNotification).not.toHaveBeenCalled();
        });
    });

    it('does not call a toast when all active models', async () => {
        modelsService.getModels = jest.fn(async () => [activeModel]);

        renderHook(() => useOpenNotificationToast(), { wrapper });

        await waitFor(() => {
            expect(mockedAddToastNotification).not.toHaveBeenCalled();
        });
    });
});
