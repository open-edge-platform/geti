// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

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
