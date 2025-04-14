// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { screen } from '@testing-library/react';

import { applicationRender as render } from '../../../test-utils/application-provider-render';
import { getMockedWorkspace } from '../../../test-utils/mocked-items-factory/mocked-workspace';
import { WorkspacesList } from './workspaces-list.component';

describe('WorkspacesList', () => {
    const workspaces = [
        getMockedWorkspace({ id: '1', name: 'Workspace 1' }),
        getMockedWorkspace({ id: '2', name: 'Workspace 2' }),
        getMockedWorkspace({ id: '3', name: 'Workspace 3' }),
        getMockedWorkspace({ id: '4', name: 'Workspace 4' }),
    ];

    it('Should list workspaces with the names and buttons to redirect to specific workspace', async () => {
        await render(<WorkspacesList workspaces={workspaces} />);

        workspaces.forEach(({ name, id }) => {
            expect(screen.getByText(name)).toBeInTheDocument();
            expect(screen.getByTestId(`workspace-${id}-see-more-button-id`)).toBeInTheDocument();
        });
    });
});
