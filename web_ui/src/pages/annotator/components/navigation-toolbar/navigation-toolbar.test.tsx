// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { fireEvent, screen, waitFor } from '@testing-library/react';

import { BooleanGroupParams } from '../../../../core/configurable-parameters/services/configurable-parameters.interface';
import { createInMemoryJobsService } from '../../../../core/jobs/services/in-memory-jobs-service';
import { JobsResponse } from '../../../../core/jobs/services/jobs-service.interface';
import { DOMAIN } from '../../../../core/projects/core.interface';
import { useProjectStatus } from '../../../../core/projects/hooks/use-project-status.hook';
import { Performance, PerformanceType, Task } from '../../../../core/projects/task.interface';
import { UserProjectSettings, UseSettings } from '../../../../core/user-settings/services/user-settings.interface';
import { useActiveLearningConfiguration } from '../../../../shared/components/header/active-learning-configuration/use-active-learning-configuration.hook';
import { fakeAnnotationToolContext } from '../../../../test-utils/fake-annotator-context';
import { getMockedProjectIdentifier } from '../../../../test-utils/mocked-items-factory/mocked-identifiers';
import { getMockedJob } from '../../../../test-utils/mocked-items-factory/mocked-jobs';
import { getMockedLabel } from '../../../../test-utils/mocked-items-factory/mocked-labels';
import { getMockedProject } from '../../../../test-utils/mocked-items-factory/mocked-project';
import { getMockedUserProjectSettingsObject } from '../../../../test-utils/mocked-items-factory/mocked-settings';
import { checkTooltip, getById, onHoverTooltip } from '../../../../test-utils/utils';
import { useProject } from '../../../project-details/providers/project-provider/project-provider.component';
import { ProjectContextProps } from '../../../project-details/providers/project-provider/project-provider.interface';
import { ANNOTATOR_MODE } from '../../core/annotation-tool-context.interface';
import { useAnnotationToolContext } from '../../providers/annotation-tool-provider/annotation-tool-provider.component';
import { useAnnotator } from '../../providers/annotator-provider/annotator-provider.component';
import { useTask } from '../../providers/task-provider/task-provider.component';
import { annotatorRender as render } from '../../test-utils/annotator-render';
import { NavigationToolbar } from './navigation-toolbar.component';

jest.mock('../../../../core/projects/hooks/use-project-status.hook', () => ({
    useProjectStatus: jest.fn(() => ({ data: { tasks: [] } })),
}));

jest.mock('../../../project-details/providers/project-provider/project-provider.component', () => ({
    ...jest.requireActual('../../../project-details/providers/project-provider/project-provider.component'),
    useProject: jest.fn(() => ({
        project: { domains: [], tasks: [] },
        isSingleDomainProject: jest.fn(),
    })),
}));

jest.mock('../../providers/annotator-provider/annotator-provider.component', () => ({
    ...jest.requireActual('../../providers/annotator-provider/annotator-provider.component'),
    useAnnotator: jest.fn(() => ({ settings: { config: {} } })),
}));

jest.mock('../../providers/annotation-tool-provider/annotation-tool-provider.component', () => ({
    ...jest.requireActual('../../providers/annotation-tool-provider/annotation-tool-provider.component'),
    useAnnotationToolContext: jest.fn(),
}));

jest.mock('../../providers/task-provider/task-provider.component', () => ({
    ...jest.requireActual('../../providers/task-provider/task-provider.component'),
    useTask: jest.fn(() => ({
        selectedTask: null,
        activeDomains: [],
        isTaskChainDomainSelected: jest.fn(),
        tasks: [],
    })),
}));

jest.mock(
    '../../../../shared/components/header/active-learning-configuration/use-active-learning-configuration.hook',
    () => ({
        useActiveLearningConfiguration: jest.fn(() => ({ autoTrainingTasks: [] })),
    })
);

const projectIdentifier = getMockedProjectIdentifier();
const fakeJobsService = createInMemoryJobsService();

describe('Navigation toolbar', () => {
    beforeAll(() => {
        fakeJobsService.getJobs = jest.fn(
            (): Promise<JobsResponse> =>
                Promise.resolve({
                    jobs: [getMockedJob()],
                    jobsCount: {
                        numberOfRunningJobs: 1,
                        numberOfFinishedJobs: 0,
                        numberOfScheduledJobs: 0,
                        numberOfCancelledJobs: 0,
                        numberOfFailedJobs: 0,
                    },
                    nextPage: '',
                })
        );

        jest.useFakeTimers();
    });

    afterAll(() => {
        jest.useRealTimers();
        jest.clearAllTimers();
    });

    beforeEach(() => {
        const annotationToolContext = fakeAnnotationToolContext({});
        (useAnnotationToolContext as jest.Mock).mockImplementation(() => annotationToolContext);
    });

    const mockSettings = getMockedUserProjectSettingsObject({
        isSavingConfig: false,
    });

    const fakeTaskOne = {
        id: 'task-1',
        title: 'Detection',
        labels: [getMockedLabel({ id: 'task-one-label' })],
        domain: DOMAIN.DETECTION,
        n_new_annotations: 2,
        required_annotations: {
            details: [],
            value: 64,
        },
    };
    const fakeTaskTwo = {
        id: 'task-2',
        title: 'Segmentation',
        labels: [getMockedLabel({ id: 'task-two-label' })],
        domain: DOMAIN.SEGMENTATION,
        n_new_annotations: 4,
        required_annotations: {
            details: [],
            value: 2,
        },
    };

    const setProjectTaskConfig = ({
        tasksConfig,
        performance,
        selectedTask,
    }: {
        selectedTask: Task | null;
        performance?: Performance;
        tasksConfig: { task: Task; isTraining: boolean; isAutoTrainingOn: boolean }[];
    }) => {
        const domains = tasksConfig.map(({ task }) => task.domain);

        jest.mocked(useProject).mockReturnValue({
            projectIdentifier,
            isTaskChainProject: domains.length > 1,
            project: getMockedProject({
                domains,
                name: 'test-project',
                tasks: tasksConfig.map(({ task }) => task),
                performance,
            }),
            isSingleDomainProject: jest.fn(),
        } as unknown as ProjectContextProps);

        (useProjectStatus as jest.Mock).mockImplementation(() => ({
            data: {
                tasks: tasksConfig.map(({ task, isTraining }) => ({ ...task, is_training: isTraining })),
            },
        }));

        jest.mocked(useActiveLearningConfiguration).mockReturnValue({
            autoTrainingTasks: tasksConfig.map(({ task, isAutoTrainingOn }) => ({
                task,
                trainingConfig: { value: isAutoTrainingOn } as BooleanGroupParams,
            })),
            isPending: false,
            updateDynamicRequiredAnnotations: jest.fn(),
            updateRequiredImagesAutoTraining: jest.fn(),
            updateAutoTraining: jest.fn(),
        });

        (useTask as jest.Mock).mockImplementation(() => ({
            selectedTask,
            activeDomains: [],
            isTaskChainDomainSelected: jest.fn(),
            tasks: tasksConfig.map(({ task }) => task),
        }));
    };

    const renderNavigationToolbar = ({
        isCreditSystemOn = false,
        ...settings
    }: UseSettings<UserProjectSettings> & { isCreditSystemOn?: boolean; isSaasEnv?: boolean }) => {
        return render(<NavigationToolbar settings={settings} />, {
            featureFlags: { FEATURE_FLAG_CREDIT_SYSTEM: isCreditSystemOn },
            services: { jobsService: fakeJobsService },
        });
    };

    it('Displays LabelSearch if is not a classification task', async () => {
        setProjectTaskConfig({
            selectedTask: null,
            tasksConfig: [{ task: fakeTaskTwo, isTraining: false, isAutoTrainingOn: true }],
        });

        (useAnnotator as jest.Mock).mockImplementation(() => ({
            mode: ANNOTATOR_MODE.ACTIVE_LEARNING,
            settings: mockSettings,
        }));

        (useTask as jest.Mock).mockImplementation(() => ({
            activeDomains: [DOMAIN.SEGMENTATION],
            isTaskChainDomainSelected: jest.fn(),
            tasks: [],
            selectedTask: {
                id: '1234',
                title: 'Segmentation',
                labels: [getMockedLabel({ id: 'task-one-label' })],
                domain: DOMAIN.SEGMENTATION,
                required_annotations: {
                    details: [],
                    value: 64,
                },
            },
        }));

        const { container } = await renderNavigationToolbar(mockSettings);

        expect(getById(container, 'label-search-field-id')).toBeTruthy();
    });

    it('Displays the project name if it is not a task chain project', async () => {
        setProjectTaskConfig({
            selectedTask: null,
            tasksConfig: [{ task: fakeTaskOne, isTraining: false, isAutoTrainingOn: true }],
        });

        await renderNavigationToolbar(mockSettings);

        expect(screen.getByTestId('project-name-domain-id')).toHaveTextContent(`test-project@ ${fakeTaskOne.domain}`);
    });

    it('Displays NavigationBreadcrumbs if it is a task chain project', async () => {
        setProjectTaskConfig({
            selectedTask: null,
            tasksConfig: [
                { task: fakeTaskOne, isTraining: false, isAutoTrainingOn: true },
                { task: fakeTaskTwo, isTraining: false, isAutoTrainingOn: true },
            ],
        });

        await renderNavigationToolbar(mockSettings);

        expect(screen.queryByRole('navigation')).toBeVisible();
    });

    it('Job management icon is properly displayed', async () => {
        setProjectTaskConfig({
            selectedTask: fakeTaskOne,
            tasksConfig: [{ task: fakeTaskOne, isTraining: false, isAutoTrainingOn: true }],
        });

        const { container } = await renderNavigationToolbar(mockSettings);

        await waitFor(() => {
            expect(getById(container, 'number-badge-running-jobs-icon')).toBeInTheDocument();
        });

        const numberBadge = getById(container, 'number-badge-running-jobs-icon');

        expect(numberBadge).toBeInTheDocument();
        expect(numberBadge).not.toHaveClass('reversedColor', { exact: false });
    });

    it('should render a GearIcon that correctly renders the settings dialog', async () => {
        setProjectTaskConfig({
            selectedTask: fakeTaskOne,
            tasksConfig: [{ task: fakeTaskOne, isTraining: false, isAutoTrainingOn: true }],
        });

        await renderNavigationToolbar(mockSettings);

        const settingsIcon = screen.getByTestId('settings-icon');
        fireEvent.click(settingsIcon);
        expect(screen.queryByLabelText('Settings dialog')).toBeTruthy();
    });

    it("shows project's performance", async () => {
        setProjectTaskConfig({
            selectedTask: fakeTaskOne,
            performance: {
                type: PerformanceType.DEFAULT,
                score: 0.1,
                taskPerformances: [
                    {
                        score: {
                            value: 0.1,
                            metricType: 'accuracy',
                        },
                        taskNodeId: 'task-id',
                    },
                ],
            },
            tasksConfig: [{ task: fakeTaskOne, isTraining: false, isAutoTrainingOn: true }],
        });

        await renderNavigationToolbar(mockSettings);

        expect(screen.getByLabelText('Project score')).toHaveAttribute('aria-valuenow', '10');

        await checkTooltip(screen.getByRole('link'), 'Latest project score');
    });

    it("shows an anomaly project's local and global performance", async () => {
        const anomalyTask: Task = { ...fakeTaskOne, domain: DOMAIN.ANOMALY_DETECTION };

        setProjectTaskConfig({
            selectedTask: anomalyTask,
            performance: {
                type: PerformanceType.ANOMALY,
                globalScore: 0.9,
                localScore: 0.4,
                score: 0.65,
                taskPerformances: [
                    {
                        taskNodeId: 'task-id',
                        score: {
                            value: 0.65,
                            metricType: 'accuracy',
                        },
                        globalScore: {
                            value: 0.9,
                            metricType: 'accuracy',
                        },
                        localScore: {
                            value: 0.4,
                            metricType: 'accuracy',
                        },
                    },
                ],
            },
            tasksConfig: [{ task: anomalyTask, isTraining: false, isAutoTrainingOn: true }],
        });

        await renderNavigationToolbar(mockSettings);

        const projectPerformanceScore = await screen.findByRole('button', { name: /project performance/i });

        jest.useFakeTimers();
        onHoverTooltip(projectPerformanceScore);
        jest.advanceTimersByTime(750);

        expect(screen.getByText(/Classification score: 90%/)).toBeInTheDocument();
        expect(screen.getByText(/Localization score: 40%/)).toBeInTheDocument();

        fireEvent.click(projectPerformanceScore);

        // TODO: fix this check (there is a <title> and a <span> being rendered with this text)
        // Probably related with the spectrum update
        expect(screen.getAllByText('Image score').at(0)).toBeInTheDocument();
        expect(screen.getByText('90%')).toBeInTheDocument();

        expect(screen.getAllByText('Object score').at(0)).toBeInTheDocument();
        expect(screen.getByText('40%')).toBeInTheDocument();
    });

    it('displays required annotation for task chain selected task', async () => {
        setProjectTaskConfig({
            selectedTask: fakeTaskOne,
            tasksConfig: [
                { task: fakeTaskOne, isTraining: false, isAutoTrainingOn: true },
                { task: fakeTaskTwo, isTraining: false, isAutoTrainingOn: true },
            ],
        });

        const { container } = await renderNavigationToolbar(mockSettings);

        expect(getById(container, 'navigation-toolbar-required-annotations')).toBeTruthy();
    });

    it('displays required annotations for task-chain All task with common auto-training "true"', async () => {
        setProjectTaskConfig({
            selectedTask: null,
            tasksConfig: [
                { task: fakeTaskOne, isTraining: false, isAutoTrainingOn: true },
                { task: fakeTaskTwo, isTraining: false, isAutoTrainingOn: true },
            ],
        });

        await renderNavigationToolbar(mockSettings);

        expect(screen.queryByTestId('required-annotations-value')).toBeInTheDocument();
        expect(screen.getByRole('button', { name: 'Active learning configuration' })).toBeInTheDocument();
    });

    it('displays required annotations for task-chain All task with common auto-training "false"', async () => {
        setProjectTaskConfig({
            selectedTask: null,
            tasksConfig: [
                { task: fakeTaskOne, isTraining: false, isAutoTrainingOn: false },
                { task: fakeTaskTwo, isTraining: false, isAutoTrainingOn: false },
            ],
        });

        await renderNavigationToolbar(mockSettings);

        expect(screen.queryByTestId('required-annotations-value')).toBeInTheDocument();
        expect(screen.getByRole('button', { name: 'Active learning configuration' })).toBeInTheDocument();
    });

    it('credit balance status is visible', async () => {
        setProjectTaskConfig({ selectedTask: null, tasksConfig: [] });
        await renderNavigationToolbar({ isCreditSystemOn: true, isSaasEnv: true, ...mockSettings });

        expect(screen.queryByRole('button', { name: 'credit balance status' })).toBeVisible();
    });
});
