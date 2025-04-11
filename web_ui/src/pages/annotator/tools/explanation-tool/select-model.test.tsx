// INTEL CONFIDENTIAL
//
// Copyright (C) 2024 Intel Corporation
//
// This software and the related documents are Intel copyrighted materials, and your use of them is governed by
// the express license under which they were provided to you ("License"). Unless the License provides otherwise,
// you may not use, modify, copy, publish, distribute, disclose or transmit this software or the related documents
// without Intel's prior written permission.
//
// This software and the related documents are provided as is, with no express or implied warranties,
// other than those that are expressly stated in the License.

import { fireEvent, screen } from '@testing-library/react';
import { userEvent } from '@testing-library/user-event';

import { DOMAIN } from '../../../../core/projects/core.interface';
import { createInMemoryProjectService } from '../../../../core/projects/services/in-memory-project-service';
import { createInMemoryUserSettingsService } from '../../../../core/user-settings/services/in-memory-user-settings-service';
import { getMockedProject } from '../../../../test-utils/mocked-items-factory/mocked-project';
import { getMockedTask } from '../../../../test-utils/mocked-items-factory/mocked-tasks';
import { projectRender as render } from '../../../../test-utils/project-provider-render';
import { SelectModel } from './select-model.component';

jest.mock('react-router-dom', () => ({
    ...jest.requireActual('react-router-dom'),
    useParams: () => ({ workspaceId: 'workspace-id', projectId: 'project-id', organizationId: 'organization-123' }),
}));

describe('SelectModel', () => {
    it('does not render without the visual prompt feature flag', async () => {
        await render(<SelectModel />, { featureFlags: { FEATURE_FLAG_VISUAL_PROMPT_SERVICE: false } });

        expect(screen.queryByRole('button')).not.toBeInTheDocument();
    });

    it('does not render for classification tasks', async () => {
        const project = getMockedProject({
            tasks: [getMockedTask({ id: '1', domain: DOMAIN.CLASSIFICATION })],
        });
        const projectService = createInMemoryProjectService();
        projectService.getProject = async () => project;

        await render(<SelectModel />, {
            services: { projectService },
            featureFlags: { FEATURE_FLAG_VISUAL_PROMPT_SERVICE: true },
        });

        expect(screen.queryByRole('button')).not.toBeInTheDocument();
    });

    it('does not render for anomaly detection task', async () => {
        const project = getMockedProject({
            tasks: [getMockedTask({ id: '1', domain: DOMAIN.ANOMALY_DETECTION })],
        });
        const projectService = createInMemoryProjectService();
        projectService.getProject = async () => project;

        await render(<SelectModel />, {
            services: { projectService },
            featureFlags: { FEATURE_FLAG_VISUAL_PROMPT_SERVICE: true },
        });

        expect(screen.queryByRole('button')).not.toBeInTheDocument();
    });

    it('does not render for task chain projects', async () => {
        const project = getMockedProject({
            tasks: [
                getMockedTask({ id: '1', domain: DOMAIN.DETECTION }),
                getMockedTask({ id: '2', domain: DOMAIN.CLASSIFICATION }),
            ],
        });
        const projectService = createInMemoryProjectService();
        projectService.getProject = async () => project;

        await render(<SelectModel />, {
            services: { projectService },
            featureFlags: { FEATURE_FLAG_VISUAL_PROMPT_SERVICE: true },
        });

        expect(screen.queryByRole('button')).not.toBeInTheDocument();
    });

    it('allows the user to switch between visual prompt and active model', async () => {
        const userSettingsService = createInMemoryUserSettingsService();

        // Get default settings, then use it to allow the test to update settings
        let settings = await userSettingsService.getProjectSettings({
            organizationId: 'organization-id',
            workspaceId: 'workspace-id',
            projectId: 'project-id',
        });
        userSettingsService.getProjectSettings = async () => {
            return settings;
        };
        userSettingsService.saveProjectSettings = async (_, newSettings) => {
            settings = newSettings;
        };

        await render(<SelectModel />, {
            featureFlags: { FEATURE_FLAG_VISUAL_PROMPT_SERVICE: true },
            services: { userSettingsService },
        });

        fireEvent.click(screen.getByRole('button'));
        const activeModel = screen.getByRole('option', { name: 'Active model' });

        await userEvent.selectOptions(screen.getByRole('listbox'), activeModel);

        fireEvent.click(await screen.findByRole('button', { name: /Active model/i }));

        const visualPromptModel = screen.getByRole('option', { name: /LVM: SAM/ });
        await userEvent.selectOptions(screen.getByRole('listbox'), visualPromptModel);

        expect(await screen.findByRole('button', { name: /LVM: SAM/i })).toBeInTheDocument();
    });
});
