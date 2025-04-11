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
