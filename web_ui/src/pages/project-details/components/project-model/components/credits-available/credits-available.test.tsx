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

import { screen, waitForElementToBeRemoved } from '@testing-library/react';

import { createInMemoryCreditsService } from '../../../../../../core/credits/services/in-memory-credits-service';
import { providersRender as render } from '../../../../../../test-utils/required-providers-render';
import { ProjectProvider } from '../../../../providers/project-provider/project-provider.component';
import { CreditsAvailable } from './credits-available.component';

describe('CreditsAvailable', () => {
    const renderApp = async ({
        contextualHelp,
        creditsAvailable,
    }: {
        contextualHelp: string;
        creditsAvailable?: number;
    }) => {
        const creditsService = createInMemoryCreditsService();

        creditsService.getOrganizationBalance = () =>
            Promise.resolve({ available: creditsAvailable as number, incoming: 100, blocked: 50 });

        render(
            <ProjectProvider
                projectIdentifier={{
                    workspaceId: 'workspace-id',
                    projectId: 'project-id',
                    organizationId: 'organization-id',
                }}
            >
                <CreditsAvailable contextualHelp={contextualHelp} />
            </ProjectProvider>,
            {
                services: { creditsService },
            }
        );

        await waitForElementToBeRemoved(screen.getAllByRole('progressbar'));
    };

    it('it is loading ', async () => {
        await renderApp({ contextualHelp: 'test' });

        expect(screen.queryByRole('button', { name: 'Information' })).not.toBeInTheDocument();
    });

    it('render available balance', async () => {
        const creditsAvailable = 10;
        await renderApp({ creditsAvailable, contextualHelp: 'test' });

        expect(await screen.findByText(`Available ${creditsAvailable} credits`)).toBeVisible();
        expect(screen.getByRole('button', { name: 'Information' })).toBeVisible();
    });
});
