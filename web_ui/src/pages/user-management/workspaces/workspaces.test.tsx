// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { screen } from '@testing-library/react';

import { useWorkspaces } from '../../../providers/workspaces-provider/workspaces-provider.component';
import { getMockedWorkspace } from '../../../test-utils/mocked-items-factory/mocked-workspace';
import { providersRender as render } from '../../../test-utils/required-providers-render';
import { Workspaces } from './workspaces.component';

jest.mock('../../../providers/workspaces-provider/workspaces-provider.component', () => ({
    ...jest.requireActual('../../../providers/workspaces-provider/workspaces-provider.component'),
    useWorkspaces: jest.fn(),
}));

describe('Workspaces', () => {
    const mockedWorkspace = getMockedWorkspace({ id: '1', name: 'Workspace 1' });
    const mockedWorkspace2 = getMockedWorkspace({ id: '2', name: 'Workspace 2' });

    it('Check if there are two workspaces displayed', async () => {
        jest.mocked(useWorkspaces).mockReturnValue({
            workspaceId: '1',
            workspaces: [mockedWorkspace, mockedWorkspace2],
        });

        await render(<Workspaces />);

        expect(screen.getByText('Workspace 1')).toBeInTheDocument();
        expect(screen.getByText('Workspace 2')).toBeInTheDocument();
    });
});
