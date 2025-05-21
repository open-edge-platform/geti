// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { screen } from '@testing-library/react';

import { ConfigurableParametersComponents } from '../../../../../core/configurable-parameters/services/configurable-parameters.interface';
import { providersRender as render } from '../../../../../test-utils/required-providers-render';
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
