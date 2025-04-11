// INTEL CONFIDENTIAL
//
// Copyright (C) 2023 Intel Corporation
//
// This software and the related documents are Intel copyrighted materials, and your use of them is governed by
// the express license under which they were provided to you ("License"). Unless the License provides otherwise,
// you may not use, modify, copy, publish, distribute, disclose or transmit this software or the related documents
// without Intel's prior written permission.
//
// This software and the related documents are provided as is, with no express or implied warranties,
// other than those that are expressly stated in the License.

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
