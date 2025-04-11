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
