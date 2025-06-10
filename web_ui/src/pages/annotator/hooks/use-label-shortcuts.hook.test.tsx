// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { waitFor } from '@testing-library/react';

import { LABEL_BEHAVIOUR } from '../../../core/labels/label.interface';
import { ProjectProps } from '../../../core/projects/project.interface';
import { createInMemoryProjectService } from '../../../core/projects/services/in-memory-project-service';
import { getMockedProjectIdentifier } from '../../../test-utils/mocked-items-factory/mocked-identifiers';
import { getMockedLabel } from '../../../test-utils/mocked-items-factory/mocked-labels';
import { getMockedProject } from '../../../test-utils/mocked-items-factory/mocked-project';
import { getMockedTask } from '../../../test-utils/mocked-items-factory/mocked-tasks';
import { renderHookWithProviders } from '../../../test-utils/render-hook-with-providers';
import { ProjectProvider } from '../../project-details/providers/project-provider/project-provider.component';
import { TaskProvider } from '../providers/task-provider/task-provider.component';
import { useLabelShortcuts } from './use-label-shortcuts.hook';

const regularLabel = getMockedLabel({ id: '1', name: 'Regular Label', behaviour: LABEL_BEHAVIOUR.LOCAL });
const exclusiveLabel = getMockedLabel({
    id: '2',
    name: 'Exclusive Label',
    behaviour: LABEL_BEHAVIOUR.EXCLUSIVE,
});
const backgroundLabel = getMockedLabel({
    id: '3',
    name: 'Background Label',
    behaviour: LABEL_BEHAVIOUR.BACKGROUND,
});
const exclusiveInSecondTaskLabel = getMockedLabel({
    id: '4',
    name: 'Exclusive in Second Task',
    behaviour: LABEL_BEHAVIOUR.EXCLUSIVE,
});

const tasks = [
    getMockedTask({ id: 'task1', labels: [regularLabel, exclusiveLabel] }),
    getMockedTask({ id: 'task2', labels: [exclusiveInSecondTaskLabel, backgroundLabel] }),
];

describe('useLabelShortcuts', () => {
    const wrapper = ({ children }: { children: React.ReactNode }) => (
        <ProjectProvider projectIdentifier={getMockedProjectIdentifier()}>
            <TaskProvider>{children}</TaskProvider>
        </ProjectProvider>
    );

    const renderApp = ({
        project,
        annotationHoleFlag,
    }: {
        project: Partial<ProjectProps>;
        annotationHoleFlag: boolean;
    }) => {
        const projectService = createInMemoryProjectService();
        projectService.getProject = async () => getMockedProject(project);

        return renderHookWithProviders(() => useLabelShortcuts(), {
            wrapper,
            providerProps: { projectService, featureFlags: { FEATURE_FLAG_ANNOTATION_HOLE: annotationHoleFlag } },
        });
    };

    describe('single task', () => {
        it('filter out background labels when FEATURE_FLAG_ANNOTATION_HOLE is false', async () => {
            const { result } = renderApp({
                project: {
                    labels: [regularLabel, exclusiveLabel, backgroundLabel],
                    tasks: [getMockedTask({ labels: [regularLabel, exclusiveLabel, backgroundLabel] })],
                },
                annotationHoleFlag: false,
            });

            await waitFor(() => {
                expect(result.current).toHaveLength(2);
                expect(result.current).toContainEqual(regularLabel);
                expect(result.current).toContainEqual(exclusiveLabel);
                expect(result.current).not.toContainEqual(backgroundLabel);
            });
        });

        it('include background labels when FEATURE_FLAG_ANNOTATION_HOLE is true', async () => {
            const { result } = renderApp({
                project: {
                    labels: [regularLabel, exclusiveLabel, backgroundLabel],
                    tasks: [getMockedTask({ labels: [regularLabel, exclusiveLabel, backgroundLabel] })],
                },
                annotationHoleFlag: true,
            });

            await waitFor(() => {
                expect(result.current).toHaveLength(3);
                expect(result.current).toContainEqual(regularLabel);
                expect(result.current).toContainEqual(exclusiveLabel);
                expect(result.current).toContainEqual(backgroundLabel);
            });
        });
    });

    describe('multiple tasks', () => {
        it('filter out background labels when FEATURE_FLAG_ANNOTATION_HOLE is false', async () => {
            const { result } = renderApp({
                project: { tasks, labels: [regularLabel, exclusiveLabel, backgroundLabel] },
                annotationHoleFlag: false,
            });

            await waitFor(() => {
                expect(result.current).toHaveLength(2);
                expect(result.current).toContainEqual(regularLabel);
                expect(result.current).toContainEqual(exclusiveLabel);
                expect(result.current).not.toContainEqual(backgroundLabel);
            });
        });

        it('include background labels when FEATURE_FLAG_ANNOTATION_HOLE is true', async () => {
            const { result } = renderApp({
                project: { tasks, labels: [regularLabel, exclusiveLabel, backgroundLabel] },
                annotationHoleFlag: true,
            });

            await waitFor(() => {
                expect(result.current).toHaveLength(3);
                expect(result.current).toContainEqual(regularLabel);
                expect(result.current).toContainEqual(exclusiveLabel);
                expect(result.current).toContainEqual(backgroundLabel);
            });
        });
    });
});
