// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { fireEvent, RenderResult, screen, waitFor, waitForElementToBeRemoved } from '@testing-library/react';
import dayjs from 'dayjs';

import { DOMAIN } from '../../../../../core/projects/core.interface';
import { PerformanceType } from '../../../../../core/projects/task.interface';
import {
    LifecycleStage,
    PerformanceCategory,
} from '../../../../../core/supported-algorithms/dtos/supported-algorithms.interface';
import { mockedDetectionSupportedAlgorithms } from '../../../../../core/supported-algorithms/services/test-utils';
import { getMockedProjectIdentifier } from '../../../../../test-utils/mocked-items-factory/mocked-identifiers';
import { getMockedModelVersion } from '../../../../../test-utils/mocked-items-factory/mocked-model';
import { getMockedProject } from '../../../../../test-utils/mocked-items-factory/mocked-project';
import { providersRender as render } from '../../../../../test-utils/required-providers-render';
import { getById } from '../../../../../test-utils/utils';
import { useTasksWithSupportedAlgorithms } from '../../../hooks/use-tasks-with-supported-algorithms';
import { ProjectProvider, useProject } from '../../../providers/project-provider/project-provider.component';
import { getModelTemplateDetails } from '../train-model-dialog/utils';
import { ModelVersion } from './model-card/model-card.interface';
import { ModelsContainer } from './models-container.component';
import { ModelContainerProps } from './models-container.interface';

jest.mock('react-router-dom', () => ({
    ...jest.requireActual('react-router-dom'),
    useNavigate: jest.fn(),
    useLocation: () => ({
        pathname:
            'localhost:3000/organizations/5b1f89f3-aba5-4a5f-84ab-de9abb8e0633/workspaces/61011e42d891c82e13ec92da/projects/123/models/1',
    }),
}));

jest.mock('../../../providers/project-provider/project-provider.component', () => ({
    ...jest.requireActual('../../../providers/project-provider/project-provider.component'),
    useProject: jest.fn(() => ({
        project: { tasks: [] },
    })),
}));

jest.mock('../../../hooks/use-tasks-with-supported-algorithms', () => ({
    useTasksWithSupportedAlgorithms: jest.fn(() => ({
        tasksWithSupportedAlgorithms: {},
    })),
}));

jest.mock('react-router-dom', () => ({
    ...jest.requireActual('react-router-dom'),
    useParams: () => ({
        projectId: 'project-123',
        workspaceId: 'workspace-123',
        organizationId: 'organization-123',
    }),
}));

describe('Model container', () => {
    beforeEach(() => {
        jest.useFakeTimers();
    });

    afterAll(() => {
        jest.useRealTimers();
        jest.clearAllTimers();
    });

    const taskId = 'task-id';

    beforeEach(() => {
        (useProject as jest.Mock).mockImplementation(() => ({
            project: getMockedProject({
                tasks: [{ id: taskId, domain: DOMAIN.DETECTION, title: 'Detection', labels: [] }],
            }),
        }));
        (useTasksWithSupportedAlgorithms as jest.Mock).mockImplementation(() => ({
            tasksWithSupportedAlgorithms: {
                [taskId]: mockedDetectionSupportedAlgorithms,
            },
        }));
    });

    const { templateName, summary } = getModelTemplateDetails(
        mockedDetectionSupportedAlgorithms[0].modelTemplateId,
        mockedDetectionSupportedAlgorithms
    );

    const defaultModelsHistory: ModelVersion[] = [
        getMockedModelVersion({
            id: '3',
            groupId: 'yolov4-id',
            groupName: 'YoloV4',
            performance: {
                type: PerformanceType.DEFAULT,
                score: 90,
            },
            version: 3,
            isActiveModel: false,
            creationDate: dayjs().toString(),
            templateName,
            isLabelSchemaUpToDate: false,
        }),
        getMockedModelVersion({
            id: '2',
            groupId: 'yolov4-id',
            groupName: 'Yolov4',
            performance: {
                type: PerformanceType.DEFAULT,
                score: 85,
            },
            version: 2,
            isActiveModel: false,
            creationDate: dayjs().toString(),
            templateName,
            isLabelSchemaUpToDate: true,
        }),
        getMockedModelVersion({
            id: '1',
            groupName: 'YoloV4',
            groupId: 'yolov4-id',
            performance: {
                type: PerformanceType.DEFAULT,
                score: 70,
            },
            version: 1,
            isActiveModel: false,
            creationDate: dayjs().toString(),
            templateName,
            isLabelSchemaUpToDate: true,
        }),
    ];

    const defaultModelOverall: ModelContainerProps = {
        modelSummary: summary,
        modelVersions: defaultModelsHistory,
        groupName: 'YoloV4',
        groupId: 'yolov4-id',
        taskId: 'task-id',
        modelTemplateId: 'model-template-Id',
        isDefaultAlgorithm: false,
        lifecycleStage: LifecycleStage.ACTIVE,
        performanceCategory: PerformanceCategory.ACCURACY,
        complexity: null,
    };

    const getMockedModelsContainer = (props: Partial<ModelContainerProps> = {}): ModelContainerProps => {
        return {
            ...defaultModelOverall,
            ...props,
        };
    };

    const renderModelContainer = async (model = getMockedModelsContainer()): Promise<RenderResult> => {
        const result = render(
            <ProjectProvider projectIdentifier={getMockedProjectIdentifier()}>
                <ModelsContainer {...model} />
            </ProjectProvider>
        );

        await waitForElementToBeRemoved(screen.getByRole('progressbar'));

        return result;
    };

    it('should render the models overall', async () => {
        const { container } = await renderModelContainer();

        expect(getById(container, `model-group-name-${defaultModelOverall.groupId}-id`)).toHaveTextContent(
            defaultModelOverall.groupName
        );
        expect(screen.getAllByTestId(/model-card-/)).toHaveLength(1);
    });

    it('should render more models after pressed expand button', async () => {
        const { container } = await renderModelContainer();

        expect(screen.getAllByTestId(/model-card-/)).toHaveLength(1);

        const expandButton = getById(container, `expand-button-${defaultModelOverall.groupId}-id`);

        expandButton && fireEvent.click(expandButton);

        expect(screen.getAllByTestId(/model-card-/)).toHaveLength(defaultModelOverall.modelVersions.length);

        expandButton && fireEvent.click(expandButton);

        await waitFor(() => {
            expect(screen.getAllByTestId(/model-card-/)).toHaveLength(1);
        });
    });

    it('should show tooltip for given algorithm', async () => {
        await renderModelContainer();

        expect(screen.queryByText(defaultModelOverall.modelSummary)).not.toBeInTheDocument();

        fireEvent.click(screen.getByRole('button', { name: 'Information' }));

        expect(await screen.findByRole('dialog')).toHaveTextContent(defaultModelOverall.modelSummary);
    });

    it('should not show expand button when there is only one model', async () => {
        const { container } = await renderModelContainer(
            getMockedModelsContainer({ modelVersions: [defaultModelsHistory[0]] })
        );
        const expandButton = getById(container, `expand-button-${defaultModelOverall.groupId}-id`);

        expect(expandButton).toBeNull();
    });

    it('should show expand button where there are at least two models', async () => {
        const { container } = await renderModelContainer();
        const expandButton = getById(container, `expand-button-${defaultModelOverall.groupId}-id`);

        expect(expandButton).toBeDefined();
    });

    it('should not show expand button when there is no model versions', async () => {
        const { container } = await renderModelContainer(getMockedModelsContainer({ modelVersions: [] }));

        const expandButton = getById(container, `expand-button-${defaultModelOverall.groupId}-id`);
        expect(expandButton).toBeNull();
    });

    it('should lower model container opacity if model is obsolete', async () => {
        const { container } = await renderModelContainer(
            getMockedModelsContainer({ lifecycleStage: LifecycleStage.OBSOLETE })
        );
        const modelsContainerWrapper = getById(container, 'models-container-yolov4-id');

        expect(modelsContainerWrapper).toHaveClass('obsolete');
    });

    it.each([
        [PerformanceCategory.SPEED, 'Recommended for speed'],
        [PerformanceCategory.BALANCE, 'Recommended for balance'],
        [PerformanceCategory.ACCURACY, 'Recommended for accuracy'],
    ])(
        'should display recommended tag with performance category if the category is different than OTHER',
        async (performanceCategory, text) => {
            await renderModelContainer(getMockedModelsContainer({ performanceCategory }));

            expect(screen.getByLabelText(text)).toBeVisible();
        }
    );

    it('should not display recommended tag if models performance category is OTHER', async () => {
        await renderModelContainer(getMockedModelsContainer({ performanceCategory: PerformanceCategory.OTHER }));

        expect(screen.queryByLabelText('Recommended for other')).not.toBeInTheDocument();
    });

    it('should display Deprecated tag if model is deprecated', async () => {
        await renderModelContainer(getMockedModelsContainer({ lifecycleStage: LifecycleStage.DEPRECATED }));

        expect(screen.getByText('Deprecated')).toBeVisible();
    });

    it('should display Obsolete tag if model is obsolete', async () => {
        await renderModelContainer(getMockedModelsContainer({ lifecycleStage: LifecycleStage.OBSOLETE }));

        expect(screen.getByText('Obsolete')).toBeVisible();
    });
});
