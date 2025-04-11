// INTEL CONFIDENTIAL
//
// Copyright (C) 2022 Intel Corporation
//
// This software and the related documents are Intel copyrighted materials, and your use of them is governed by
// the express license under which they were provided to you ("License"). Unless the License provides otherwise,
// you may not use, modify, copy, publish, distribute, disclose or transmit this software or the related documents
// without Intel's prior written permission.
//
// This software and the related documents are provided as is, with no express or implied warranties,
// other than those that are expressly stated in the License.

import { screen } from '@testing-library/react';

import { providersRender as render } from '../../../../../test-utils/required-providers-render';
import { ConfigurableParametersComponents } from '../../configurable-parameters.interface';
import { SelectableTabContent } from './selectable-tab-content.component';

describe('Selectable tab content', () => {
    const selectedComponentMock: ConfigurableParametersComponents = {
        description: 'This is description of the configurable parameter',
        entityIdentifier: {
            component: 'PROJECT_ACTIVE_LEARNING',
            projectId: 'project-123',
            taskId: undefined,
            type: 'COMPONENT_PARAMETERS',
            workspaceId: '1234567890',
        },
        id: 'id',
        header: 'Header',
        parameters: [],
        groups: [],
    };

    it('Check if description is visible', async () => {
        render(<SelectableTabContent updateParameter={jest.fn()} selectedComponent={selectedComponentMock} />);

        const description = screen.getByText(selectedComponentMock.description);
        expect(description).toBeInTheDocument();
    });
});
