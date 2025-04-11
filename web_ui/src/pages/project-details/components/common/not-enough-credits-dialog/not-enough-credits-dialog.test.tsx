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
