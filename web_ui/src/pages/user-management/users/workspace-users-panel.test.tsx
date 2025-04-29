// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { screen } from '@testing-library/react';

import { applicationRender as render } from '../../../test-utils/application-provider-render';
import { getMockedWorkspace } from '../../../test-utils/mocked-items-factory/mocked-workspace';
import { WorkspaceUsersPanel } from './workspace-users-panel.component';

const mockedSelectedWorkspace = jest.fn();
const mockedWorkspace = getMockedWorkspace({ name: 'Default', id: 'default-workspace-id' });

jest.mock('../../../providers/workspaces-provider/workspaces-provider.component', () => ({
    ...jest.requireActual('../../../providers/workspaces-provider/workspaces-provider.component'),
    useWorkspaces: jest.fn(() => ({ workspaces: [mockedWorkspace] })),
}));

describe('WorkspaceUsersPanel', () => {
    it('Select first if there is no possibility to create more workspaces', async () => {
        await render(
            <WorkspaceUsersPanel selectedWorkspace={undefined} setSelectedWorkspace={mockedSelectedWorkspace} />,
            {
                featureFlags: { FEATURE_FLAG_WORKSPACE_ACTIONS: false },
            }
        );

        expect(mockedSelectedWorkspace).toHaveBeenCalledWith(mockedWorkspace.id);
        expect(screen.getByTestId('select-workspace-users-list-id')).toBeDisabled();
    });
});
