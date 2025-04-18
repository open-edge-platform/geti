// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { waitFor } from '@testing-library/react';

import { createInMemoryProjectService } from '../../../../../core/projects/services/in-memory-project-service';
import { getMockedKeypointNode } from '../../../../../test-utils/mocked-items-factory/mocked-keypoint';
import { getMockedLabel } from '../../../../../test-utils/mocked-items-factory/mocked-labels';
import { getMockedProject } from '../../../../../test-utils/mocked-items-factory/mocked-project';
import { getMockedKeypointTask } from '../../../../../test-utils/mocked-items-factory/mocked-tasks';
import { renderHookWithProviders } from '../../../../../test-utils/render-hook-with-providers';
import { useGetProjectsTemplates } from './use-get-projects-templates.hook';

describe('useGetProjectsTemplates', () => {
    it('returns an empty result when there are no keypoint projects', () => {
        const projectService = createInMemoryProjectService();

        const { result } = renderHookWithProviders(() => useGetProjectsTemplates(), {
            providerProps: { projectService },
        });

        expect(result.current).toHaveLength(0);
    });

    it('provides templates for keypoint projects', async () => {
        const point1 = getMockedKeypointNode({ label: getMockedLabel({ id: 'id-label-1', name: 'label 1' }) });
        const point2 = getMockedKeypointNode({ label: getMockedLabel({ id: 'id-label-2', name: 'label 2' }) });

        const projects = [
            getMockedProject({
                id: '1',
                name: 'Project-1',
                tasks: [
                    getMockedKeypointTask({
                        keypointStructure: {
                            edges: [{ nodes: [point1.label.id, point2.label.id] }],
                            positions: [point1, point2],
                        },
                        labels: [point1.label, point2.label],
                    }),
                ],
            }),
            getMockedProject({
                id: '2',
                name: 'Project-2',
                tasks: [
                    getMockedKeypointTask({
                        keypointStructure: {
                            edges: [{ nodes: [point2.label.id, point1.label.id] }],
                            positions: [point1, point2],
                        },
                        labels: [point1.label, point2.label],
                    }),
                ],
            }),
        ];

        const projectService = createInMemoryProjectService();
        projectService.getProjects = async () => ({ projects, nextPage: null });

        const { result } = renderHookWithProviders(() => useGetProjectsTemplates(), {
            providerProps: { projectService },
        });

        await waitFor(() => {
            expect(result.current).toEqual([
                {
                    name: projects[0].name,
                    template: {
                        edges: [{ from: point1.label.name, to: point2.label.name }],
                        points: [
                            { label: point1.label.name, x: point1.x, y: point1.y },
                            { label: point2.label.name, x: point2.x, y: point2.y },
                        ],
                    },
                },
                {
                    name: projects[1].name,
                    template: {
                        edges: [{ from: point2.label.name, to: point1.label.name }],
                        points: [
                            { label: point1.label.name, x: point1.x, y: point1.y },
                            { label: point2.label.name, x: point2.x, y: point2.y },
                        ],
                    },
                },
            ]);
        });
    });
});
