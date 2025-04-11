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

import { createInMemoryCreditsService } from '../../../../../core/credits/services/in-memory-credits-service';
import { createInMemoryProjectService } from '../../../../../core/projects/services/in-memory-project-service';
import {
    getMockedProjectStatus,
    getMockedProjectStatusTask,
} from '../../../../../test-utils/mocked-items-factory/mocked-project';
import { providersRender as render } from '../../../../../test-utils/required-providers-render';
import { useTotalCreditPrice } from '../../../hooks/use-credits-to-consume.hook';
import { ProjectProvider } from '../../../providers/project-provider/project-provider.component';
import { CreditBalanceTrainDialog } from './credit-balance-train-dialog.component';

jest.mock('../../../hooks/use-credits-to-consume.hook', () => ({
    useTotalCreditPrice: jest.fn(),
}));

const projectIdentifier = {
    projectId: 'project-id',
    workspaceId: 'workspace-id',
    organizationId: 'organization-id',
};

describe('CreditBalanceTrainDialog', (): void => {
    beforeEach((): void => {
        jest.clearAllMocks();
    });

    const renderComponent = async ({
        creditFlag = true,
        creditsAvailable,
        totalCreditsToConsume,
        onClose = jest.fn(),
    }: {
        creditFlag?: boolean;
        creditsAvailable?: number;
        totalCreditsToConsume?: number;
        onClose?: jest.Mock;
    }): Promise<void> => {
        const creditsService = createInMemoryCreditsService();
        const projectService = createInMemoryProjectService();
        projectService.getProjectStatus = () =>
            Promise.resolve(
                getMockedProjectStatus({ tasks: [getMockedProjectStatusTask({ id: '1', ready_to_train: true })] })
            );

        creditsService.getOrganizationBalance = () =>
            Promise.resolve({ available: creditsAvailable as number, incoming: 100, blocked: 0 });

        jest.mocked(useTotalCreditPrice).mockReturnValue({
            getCreditPrice: () => ({ totalCreditsToConsume: totalCreditsToConsume as number, totalMedias: 1 }),
            isLoading: false,
        });

        render(
            <ProjectProvider projectIdentifier={projectIdentifier}>
                <CreditBalanceTrainDialog isOpen onClose={onClose} />
            </ProjectProvider>,
            { services: { creditsService, projectService }, featureFlags: { FEATURE_FLAG_CREDIT_SYSTEM: creditFlag } }
        );
        await waitForElementToBeRemoved(screen.getByRole('progressbar'));
    };

    it('render TrainModelDialog', async (): Promise<void> => {
        await renderComponent({ totalCreditsToConsume: 10, creditsAvailable: 20 });

        expect(await screen.findByText(/select template/i)).toBeVisible();
    });

    it('flag is off, render TrainModelDialog', async (): Promise<void> => {
        await renderComponent({ totalCreditsToConsume: 10, creditsAvailable: 9, creditFlag: false });

        expect(await screen.findByText(/select template/i)).toBeVisible();
    });

    it('render NotEnoughCreditsDialog', async (): Promise<void> => {
        await renderComponent({ totalCreditsToConsume: 10, creditsAvailable: 9 });

        expect(await screen.findByText(/not enough credits/i)).toBeVisible();
    });
});
