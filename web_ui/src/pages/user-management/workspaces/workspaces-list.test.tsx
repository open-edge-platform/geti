// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { screen } from '@testing-library/react';

import { applicationRender as render } from '../../../test-utils/application-provider-render';
import { getMockedWorkspace } from '../../../test-utils/mocked-items-factory/mocked-workspace';
import { useDefaultWorkspace } from '../../landing-page/workspaces-tabs/use-default-workspace.hook';
import { WorkspacesList } from './workspaces-list.component';

jest.mock('../../landing-page/workspaces-tabs/use-default-workspace.hook', () => ({
    useDefaultWorkspace: jest.fn(),
}));

describe('WorkspacesList', () => {
    const mockedWorkspaces = [
        getMockedWorkspace({ id: '1', name: 'Workspace 1' }),
        getMockedWorkspace({ id: '2', name: 'Workspace 2' }),
        getMockedWorkspace({ id: '3', name: 'Workspace 3' }),
        getMockedWorkspace({ id: '4', name: 'Workspace 4' }),
    ];

    it('Should list workspaces with the names and buttons to redirect to specific workspace', async () => {
        jest.mocked(useDefaultWorkspace).mockReturnValue({
            defaultWorkspaceId: '1',
            reorderedWorkspaces: mockedWorkspaces,
        });
        await render(<WorkspacesList workspaces={mockedWorkspaces} />);

        mockedWorkspaces.forEach(({ name, id }) => {
            expect(screen.getByText(name)).toBeInTheDocument();
            expect(screen.getByTestId(`workspace-${id}-see-more-button-id`)).toBeInTheDocument();
        });
    });

    it('Should shown indicator next to the name of default workspace', async () => {
        jest.mocked(useDefaultWorkspace).mockReturnValue({
            defaultWorkspaceId: '2',
            reorderedWorkspaces: mockedWorkspaces,
        });
        await render(<WorkspacesList workspaces={mockedWorkspaces} />, {
            featureFlags: { FEATURE_FLAG_WORKSPACE_ACTIONS: true },
        });

        expect(screen.getByTestId('Workspace 2-default-workspace-indicator')).toBeInTheDocument();
    });
});
