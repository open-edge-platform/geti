// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { fireEvent, screen, waitForElementToBeRemoved } from '@testing-library/react';

import { CONTACT_SUPPORT } from '../../../../../core/const';
import { openNewTab } from '../../../../../shared/utils';
import { providersRender as render } from '../../../../../test-utils/required-providers-render';
import { ProjectProvider } from '../../../providers/project-provider/project-provider.component';
import { NotEnoughCreditsDialog } from './not-enough-credits-dialog.component';

jest.mock('../../../../../shared/utils', () => ({
    ...jest.requireActual('../../../../../shared/utils'),
    openNewTab: jest.fn(),
}));

describe('NotEnoughCreditsDialog', (): void => {
    beforeEach((): void => {
        jest.clearAllMocks();
    });

    const renderComponent = async ({
        isOpen,
        onClose = jest.fn(),
    }: {
        isOpen: boolean;
        onClose?: jest.Mock;
    }): Promise<void> => {
        render(
            <ProjectProvider
                projectIdentifier={{
                    projectId: 'project-id',
                    workspaceId: 'workspace-id',
                    organizationId: 'organization-id',
                }}
            >
                <NotEnoughCreditsDialog
                    isOpen={isOpen}
                    onClose={onClose}
                    creditsToConsume={20}
                    creditsAvailable={20}
                    message={{ header: 'header message:', body: 'body message' }}
                />
            </ProjectProvider>
        );
        await waitForElementToBeRemoved(screen.getByRole('progressbar'));
    };

    it('close modal', async (): Promise<void> => {
        const onClose = jest.fn();
        await renderComponent({ isOpen: true, onClose });

        fireEvent.click(screen.getByRole('button', { name: /close/i }));

        expect(onClose).toHaveBeenCalled();
        expect(openNewTab).not.toHaveBeenCalled();
    });

    it('open Contact support in a new tap', async (): Promise<void> => {
        const onClose = jest.fn();
        await renderComponent({ isOpen: true, onClose });

        fireEvent.click(screen.getByRole('button', { name: /contact support/i }));

        expect(openNewTab).toHaveBeenCalledWith(CONTACT_SUPPORT);
        expect(onClose).toHaveBeenCalled();
    });
});
