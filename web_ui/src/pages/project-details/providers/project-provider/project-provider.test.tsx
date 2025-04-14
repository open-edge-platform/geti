// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { ReactNode } from 'react';

import { waitFor } from '@testing-library/react';

import { DOMAIN } from '../../../../core/projects/core.interface';
import { isClassificationDomain, isDetectionDomain } from '../../../../core/projects/domains';
import { createInMemoryProjectService } from '../../../../core/projects/services/in-memory-project-service';
import { Task } from '../../../../core/projects/task.interface';
import { getMockedProjectIdentifier } from '../../../../test-utils/mocked-items-factory/mocked-identifiers';
import { getMockedProject } from '../../../../test-utils/mocked-items-factory/mocked-project';
import { getMockedTask } from '../../../../test-utils/mocked-items-factory/mocked-tasks';
import { renderHookWithProviders } from '../../../../test-utils/render-hook-with-providers';
import { ProjectProvider, useProject } from './project-provider.component';

describe('project provider', () => {
    const wrapper = ({ children }: { children?: ReactNode }) => {
        return (
            <ProjectProvider
                projectIdentifier={getMockedProjectIdentifier({ projectId: 'test', workspaceId: 'test_workspace' })}
            >
                {children}
            </ProjectProvider>
        );
    };

    const renderProjectHook = ({ tasks }: { tasks: Task[] }) => {
        const projectService = createInMemoryProjectService();

        projectService.getProject = jest.fn(async () => {
            return getMockedProject({ id: 'test', tasks });
        });

        return renderHookWithProviders(useProject, {
            wrapper: ({ children }) => wrapper({ children }),
            providerProps: { projectService },
        });
    };

    describe('isTaskChainProject', () => {
        it('is not a task chain project if there is only a single task', async () => {
            const tasks = [getMockedTask({ id: 'classification', domain: DOMAIN.CLASSIFICATION })];

            const { result } = renderProjectHook({ tasks });

            // Wait for project to be loaded
            await waitFor(() => {
                expect(result.current.project).not.toBeUndefined();
            });

            expect(result.current.isTaskChainProject).toBe(false);
        });

        it('is a task chain project if there are multiple tasks', async () => {
            const tasks = [
                getMockedTask({ id: 'detection', domain: DOMAIN.DETECTION }),
                getMockedTask({ id: 'classification', domain: DOMAIN.CLASSIFICATION }),
            ];

            const { result } = renderProjectHook({ tasks });

            // Wait for project to be loaded
            await waitFor(() => {
                expect(result.current.project).not.toBeUndefined();
            });

            expect(result.current.isTaskChainProject).toBe(true);
        });
    });

    describe('isSingleDomainProject', () => {
        it('is not a single domain project if there are multiple tasks', async () => {
            const tasks = [
                getMockedTask({ id: 'detection', domain: DOMAIN.DETECTION }),
                getMockedTask({ id: 'classification', domain: DOMAIN.CLASSIFICATION }),
            ];

            const { result } = renderProjectHook({ tasks });

            // Wait for project to be loaded
            await waitFor(() => {
                expect(result.current.project).not.toBeUndefined();
            });

            expect(result.current.isSingleDomainProject(DOMAIN.CLASSIFICATION)).toBe(false);
            expect(result.current.isSingleDomainProject(isClassificationDomain)).toBe(false);
        });

        it('is a single domain project if there is a single task', async () => {
            const tasks = [getMockedTask({ id: 'classification', domain: DOMAIN.CLASSIFICATION })];

            const { result } = renderProjectHook({ tasks });

            // Wait for project to be loaded
            await waitFor(() => {
                expect(result.current.project).not.toBeUndefined();
            });

            expect(result.current.isSingleDomainProject(DOMAIN.CLASSIFICATION)).toBe(true);
            expect(result.current.isSingleDomainProject(isClassificationDomain)).toBe(true);

            expect(result.current.isSingleDomainProject(DOMAIN.DETECTION)).toBe(false);
            expect(result.current.isSingleDomainProject(isDetectionDomain)).toBe(false);
        });
    });
});
