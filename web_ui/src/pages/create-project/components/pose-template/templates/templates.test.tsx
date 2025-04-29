// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { fireEvent, render, screen, waitFor } from '@testing-library/react';

import { createInMemoryProjectService } from '../../../../../core/projects/services/in-memory-project-service';
import { getMockedKeypointNode } from '../../../../../test-utils/mocked-items-factory/mocked-keypoint';
import { getMockedLabel } from '../../../../../test-utils/mocked-items-factory/mocked-labels';
import { getMockedProject } from '../../../../../test-utils/mocked-items-factory/mocked-project';
import { getMockedKeypointTask } from '../../../../../test-utils/mocked-items-factory/mocked-tasks';
import { RequiredProviders } from '../../../../../test-utils/required-providers-render';
import { Templates } from './templates.component';
import { formatTemplate, TemplatePose } from './utils';

jest.mock('./utils', () => ({
    ...jest.requireActual('./utils'),
    formatTemplate: jest.fn((data) => data),
}));

const point1 = getMockedKeypointNode({ label: getMockedLabel({ id: 'id-label-1', name: 'label 1' }) });
const point2 = getMockedKeypointNode({ label: getMockedLabel({ id: 'id-label-2', name: 'label 2' }) });
const mockedKeypointTask = getMockedKeypointTask({
    keypointStructure: {
        edges: [{ nodes: [point1.label.id, point2.label.id] }],
        positions: [point1, point2],
    },
    labels: [point1.label, point2.label],
});

const projects = [
    getMockedProject({
        id: '1',
        name: 'Project-1',
        tasks: [mockedKeypointTask],
    }),
];

describe('Templates', () => {
    const mockedRoi = { x: 0, y: 0, width: 1000, height: 1000 };

    const renderApp = (onAction: jest.Mock, projectService = createInMemoryProjectService()) => {
        render(
            <RequiredProviders projectService={projectService}>
                <Templates roi={mockedRoi} onAction={onAction} />
            </RequiredProviders>
        );
    };

    it.each([[TemplatePose.HumanPose], [TemplatePose.AnimalPose], [TemplatePose.HumanFace]])(
        'calls %s and onAction when "%s" is selected',
        (templateName) => {
            const mockedAction = jest.fn();

            renderApp(mockedAction);

            fireEvent.click(screen.getByRole('button', { name: 'templates list' }));
            fireEvent.click(screen.getByRole('menuitem', { name: templateName }));

            expect(mockedAction).toHaveBeenCalled();
            expect(formatTemplate).toHaveBeenCalled();
        }
    );

    it('displays project templates correctly', async () => {
        const mockedAction = jest.fn();
        const mockedProjectService = createInMemoryProjectService();
        mockedProjectService.getProjects = async () => ({ projects, nextPage: null });

        renderApp(mockedAction, mockedProjectService);

        fireEvent.click(screen.getByRole('button', { name: 'templates list' }));

        await waitFor(() => {
            expect(screen.getByRole('group', { name: 'Project templates' })).toBeVisible();
            expect(screen.getByRole('group', { name: 'Geti templates' })).toBeVisible();

            fireEvent.click(screen.getByRole('menuitem', { name: projects.at(-1)?.name }));
        });

        expect(formatTemplate).toHaveBeenCalled();
        expect(mockedAction).toHaveBeenCalled();
    });
});
