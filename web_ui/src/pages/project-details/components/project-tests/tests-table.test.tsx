// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { screen, waitForElementToBeRemoved } from '@testing-library/react';

import { getMockedTest } from '../../../../core/tests/services/tests-utils';
import { Test } from '../../../../core/tests/tests.interface';
import { providersRender as render } from '../../../../test-utils/required-providers-render';
import { ProjectProvider } from '../../providers/project-provider/project-provider.component';
import { TestsTable } from './tests-table.component';

jest.mock('../../../../hooks/use-project-identifier/use-project-identifier', () => {
    return {
        useProjectIdentifier: jest.fn(() => ({
            projectId: 'project-id',
            workspaceId: 'workspace-id',
            organizationId: 'organization-id',
        })),
    };
});

describe('TestsTable', () => {
    const renderApp = async (tests: Test[], projectId = 'project-id', isLoading = false) => {
        render(
            <ProjectProvider
                projectIdentifier={{
                    organizationId: 'organization-id',
                    workspaceId: 'workspace-id',
                    projectId,
                }}
            >
                <TestsTable tests={tests} isLoading={isLoading} />
            </ProjectProvider>
        );

        await waitForElementToBeRemoved(screen.getByRole('progressbar'));
    };

    it('"NoTests" is visible if the test list is empty', async () => {
        await renderApp([]);

        expect(screen.getByRole('heading', { name: 'No tests' })).toBeVisible();
        expect(screen.queryByRole('grid', { name: 'Table with testing sets' })).not.toBeInTheDocument();
    });

    it('test list is visible', async () => {
        await renderApp([getMockedTest({ testName: 'test 1' })]);

        expect(screen.getByRole('grid', { name: 'Table with testing sets' })).toBeVisible();
        expect(screen.getByRole('row', { name: 'test 1' })).toBeVisible();
    });

    it('does not display "Task type" column for single-chain project', async () => {
        await renderApp([getMockedTest({ testName: 'test 1' })]);

        expect(screen.getByRole('columnheader', { name: 'Name' })).toBeVisible();
        expect(screen.queryByRole('columnheader', { name: 'Task type' })).not.toBeInTheDocument();
    });

    it('displays "Task type" column for task-chain project', async () => {
        await renderApp([getMockedTest({ testName: 'test 1' })], 'project-task-chain-id');

        expect(screen.getByRole('columnheader', { name: 'Name' })).toBeVisible();
        expect(screen.getByRole('columnheader', { name: 'Task type' })).toBeVisible();
    });
});
