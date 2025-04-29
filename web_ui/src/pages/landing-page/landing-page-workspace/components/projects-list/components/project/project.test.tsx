// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { dimensionValue } from '@react-spectrum/utils';
import { fireEvent, screen, waitFor } from '@testing-library/react';
import localforage from 'localforage';

import { LABEL_BEHAVIOUR } from '../../../../../../../core/labels/label.interface';
import { DOMAIN } from '../../../../../../../core/projects/core.interface';
import { createInMemoryProjectService } from '../../../../../../../core/projects/services/in-memory-project-service';
import { PerformanceType } from '../../../../../../../core/projects/task.interface';
import { getMockedLabel, mockedLongLabels } from '../../../../../../../test-utils/mocked-items-factory/mocked-labels';
import { getMockedProject } from '../../../../../../../test-utils/mocked-items-factory/mocked-project';
import { getMockedTask } from '../../../../../../../test-utils/mocked-items-factory/mocked-tasks';
import { projectListRender as render } from '../../../../../../../test-utils/projects-list-providers-render';
import { getById } from '../../../../../../../test-utils/utils';
import { GETI_CAMERA_INDEXEDDB_INSTANCE_NAME } from '../../../../../../camera-support/camera.interface';
import { Project } from './project.component';

jest.mock('../../../../../../../shared/components/has-permission/has-permission.component', () => ({
    ...jest.requireActual('../../../../../../../shared/components/has-permission/has-permission.component'),
    useCheckPermission: () => true,
}));

jest.mock('react-router-dom', () => ({
    ...jest.requireActual('react-router-dom'),
    useParams: () => ({ organizationId: 'organization-id', workspaceId: 'workspace-id' }),
}));

describe('Project', () => {
    it('Check name and domain string when there are two domains', async () => {
        const mockProject = getMockedProject({
            id: '1111',
            domains: [DOMAIN.CLASSIFICATION, DOMAIN.DETECTION],
        });
        const { container } = await render(<Project project={mockProject} />);

        const projectNameContainer = getById(container, 'project-name-test-project-1');
        const projectName = projectNameContainer?.textContent;

        expect(projectName).toBe(`Test project 1`);
    });

    it('check name and domain string when there is one domain', async () => {
        const mockProject = getMockedProject({ id: '2222', domains: [DOMAIN.CLASSIFICATION] });
        const { container } = await render(<Project project={mockProject} />);

        const projectNameContainer = getById(container, 'project-name-test-project-1');
        const projectName = projectNameContainer?.textContent;

        expect(projectName).toBe(`Test project 1`);
    });

    it('check if empty label were filtered out', async () => {
        const labels = [
            getMockedLabel({ id: '1', name: 'cat' }),
            getMockedLabel({ id: '2', name: 'dog' }),
            getMockedLabel({ id: '3', name: 'Some random name', isEmpty: true }),
        ];

        const mockProject = getMockedProject({
            name: 'test project',
            tasks: [getMockedTask({ domain: DOMAIN.CLASSIFICATION, labels })],
        });

        await render(<Project project={mockProject} />);

        const filteredOutLabel = screen.queryByText('Some random name');

        expect(screen.queryByText('cat')).toBeTruthy();
        expect(screen.queryByText('dog')).toBeTruthy();
        expect(filteredOutLabel).toBeFalsy();
    });

    it('check if long labels are displayed properly', async () => {
        const mockProject = getMockedProject({
            name: 'project with long labels',
            tasks: [getMockedTask({ domain: DOMAIN.CLASSIFICATION, labels: mockedLongLabels })],
        });

        await render(<Project project={mockProject} />);

        expect(screen.getByText(mockProject.labels[0].name)).toHaveStyle('text-overflow: ellipsis');
        expect(screen.getByText(mockProject.labels[1].name)).toHaveStyle('text-overflow: ellipsis');
        expect(screen.getByText(mockProject.labels[2].name)).toHaveStyle('text-overflow: ellipsis');

        expect(screen.getByText(mockProject.labels[0].name)).toHaveStyle(`maxWidth: ${dimensionValue('size-2400')}`);
        expect(screen.getByText(mockProject.labels[1].name)).toHaveStyle(`maxWidth: ${dimensionValue('size-2400')}`);
        expect(screen.getByText(mockProject.labels[2].name)).toHaveStyle(`maxWidth: ${dimensionValue('size-2400')}`);
    });

    it('Shows normal and anomalous labels', async () => {
        const labels = [
            getMockedLabel({ id: '1', name: 'Normal', behaviour: LABEL_BEHAVIOUR.GLOBAL + LABEL_BEHAVIOUR.EXCLUSIVE }),
            getMockedLabel({
                id: '2',
                name: 'Anomalous',
                behaviour: LABEL_BEHAVIOUR.GLOBAL + LABEL_BEHAVIOUR.LOCAL + LABEL_BEHAVIOUR.ANOMALOUS,
            }),
        ];

        const mockProject = getMockedProject({
            name: 'test project',
            tasks: [getMockedTask({ domain: DOMAIN.ANOMALY_CLASSIFICATION, labels })],
        });

        await render(<Project project={mockProject} />);

        expect(screen.queryByText('Normal')).toBeTruthy();
        expect(screen.queryByText('Anomalous')).toBeTruthy();
    });

    it('Shows project score for single task', async () => {
        const mockProject = getMockedProject({
            id: '1111',
            domains: [DOMAIN.DETECTION],
            performance: {
                score: 0.3,
                type: PerformanceType.DEFAULT,
                taskPerformances: [
                    {
                        domain: DOMAIN.DETECTION,
                        taskNodeId: 'task-id',
                        score: {
                            value: 0.3,
                            metricType: 'accuracy',
                        },
                    },
                ],
            },
        });

        await render(<Project project={mockProject} />);

        const performance = screen.getByLabelText('Metric type: accuracy');

        expect(performance).toBeVisible();
        expect(performance).toHaveAttribute('aria-valuenow', '30');
    });

    it('Shows project score for task chain', async () => {
        const mockProject = getMockedProject({
            id: '1111',
            domains: [DOMAIN.DETECTION, DOMAIN.SEGMENTATION],
            tasks: [
                getMockedTask({ id: 'detection-id', domain: DOMAIN.DETECTION }),
                getMockedTask({ id: 'segmentation-id', domain: DOMAIN.SEGMENTATION }),
            ],
            performance: {
                score: 0.65,
                type: PerformanceType.DEFAULT,
                taskPerformances: [
                    {
                        domain: DOMAIN.DETECTION,
                        taskNodeId: 'detection-id',
                        score: {
                            value: 0.7,
                            metricType: 'f-measure',
                        },
                    },
                    {
                        domain: DOMAIN.SEGMENTATION,
                        taskNodeId: 'segmentation-id',
                        score: {
                            value: 0.6,
                            metricType: 'accuracy',
                        },
                    },
                ],
            },
        });

        await render(<Project project={mockProject} />);

        const performanceDetection = screen.getByLabelText('Detection - metric type: f-measure');
        const performanceSegmentation = screen.getByLabelText('Segmentation - metric type: accuracy');

        expect(performanceDetection).toBeVisible();
        expect(performanceDetection).toHaveAttribute('aria-valuenow', '70');

        expect(performanceSegmentation).toBeVisible();
        expect(performanceSegmentation).toHaveAttribute('aria-valuenow', '60');
    });

    it('Shows SkeletonLoader if the project is being deleted', async () => {
        const mockProject = getMockedProject({
            id: '1111',
            domains: [DOMAIN.CLASSIFICATION],
        });

        const projectService = createInMemoryProjectService();
        projectService.deleteProject = jest.fn(async () => {
            return new Promise(() => 'We dont resolve this so that we can show a skeleton');
        });
        await render(<Project project={mockProject} />, { services: { projectService } });

        // Open menu
        fireEvent.click(screen.getByRole('button', { name: 'action menu' }));

        // Trigger dialog
        fireEvent.click(screen.getByText('Delete'));

        // Confirm deletion
        await waitFor(() => {
            expect(screen.getByRole('button', { name: 'Delete' })).toBeEnabled();
        });
        fireEvent.click(screen.getByRole('button', { name: 'Delete' }));

        await waitFor(() => {
            expect(screen.getByTestId('project-item-loader-list')).toBeInTheDocument();
        });
        expect(projectService.deleteProject).toHaveBeenCalled();
    });

    it('Clears the project storage after being deleted', async () => {
        const localforageSpy = jest.spyOn(localforage, 'dropInstance');

        const mockProject = getMockedProject({
            id: '1111',
            domains: [DOMAIN.CLASSIFICATION],
        });

        const projectService = createInMemoryProjectService();
        projectService.deleteProject = jest.fn(() => Promise.resolve(''));
        projectService.getProject = jest.fn().mockResolvedValue(mockProject);
        await render(<Project project={mockProject} />, { services: { projectService } });

        // Open menu
        fireEvent.click(screen.getByRole('button', { name: 'action menu' }));

        // Trigger dialog
        fireEvent.click(screen.getByText('Delete'));

        // Confirm deletion
        await waitFor(() => {
            expect(screen.getByRole('button', { name: 'Delete' })).toBeEnabled();
        });
        fireEvent.click(screen.getByRole('button', { name: 'Delete' }));

        await waitFor(() => {
            expect(localforageSpy).toHaveBeenNthCalledWith(1, {
                storeName: `dataset-${mockProject.datasets.at(0)?.id}`,
                name: GETI_CAMERA_INDEXEDDB_INSTANCE_NAME,
            });
        });
    });
});
