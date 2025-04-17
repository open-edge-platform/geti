// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { screen, waitForElementToBeRemoved } from '@testing-library/react';

import { createInMemoryCreditsService } from '../../../../../../core/credits/services/in-memory-credits-service';
import { createInMemoryModelsService } from '../../../../../../core/models/services/in-memory-models-service';
import { getMockedProjectIdentifier } from '../../../../../../test-utils/mocked-items-factory/mocked-identifiers';
import { providersRender } from '../../../../../../test-utils/required-providers-render';
import { useTotalCreditPrice } from '../../../../hooks/use-credits-to-consume.hook';
import { ProjectProvider } from '../../../../providers/project-provider/project-provider.component';
import { ActivateModelDialog } from './activate-model-dialog.component';

jest.mock('../../../../hooks/use-credits-to-consume.hook', () => ({
    useTotalCreditPrice: jest.fn(),
}));

jest.mock('../../legacy-train-model-dialog/use-training-state-value/use-training-state-value.hook', () => ({
    ...jest.requireActual('../../legacy-train-model-dialog/use-training-state-value/use-training-state-value.hook'),
}));

describe('ActivateModelDialog', () => {
    beforeEach(() => {
        jest.clearAllMocks();
    });

    const creditsService = createInMemoryCreditsService();
    const modelsService = createInMemoryModelsService();

    const render = async ({ featureFlags = { FEATURE_FLAG_CREDIT_SYSTEM: true } }) => {
        providersRender(
            <ProjectProvider projectIdentifier={getMockedProjectIdentifier()}>
                <ActivateModelDialog
                    modelName={'test-model'}
                    isOpen={true}
                    modelVersion={1}
                    createdAt={'2024-09-11T09:13:57Z'}
                    handleDismiss={jest.fn()}
                    handleActivateModel={jest.fn()}
                    handleActivateAndRetrainModel={jest.fn()}
                />
            </ProjectProvider>,
            {
                featureFlags,
                services: { modelsService, creditsService },
            }
        );

        await waitForElementToBeRemoved(screen.getByRole('progressbar'));
    };

    it('displays ActivateModelDialog and informs about number of deduced credits when FEATURE_FLAG_CREDIT_SYSTEM is enabled', async () => {
        jest.mocked(useTotalCreditPrice).mockReturnValue({
            getCreditPrice: () => ({ totalCreditsToConsume: 12, totalMedias: 1 }),
            isLoading: false,
        });

        await render({});

        expect(
            screen.getByText(/The selected model - test-model - Version 1 from 2024-09-11T09:13:57Z - was trained/)
        ).toBeInTheDocument();
        expect(screen.getByText(/12 credits will be deducted./)).toBeInTheDocument();
    });

    it('displays ActivateModelDialog without credit information when FEATURE_FLAG_CREDIT_SYSTEM is disabled', async () => {
        await render({ featureFlags: { FEATURE_FLAG_CREDIT_SYSTEM: false } });

        expect(
            screen.getByText(/The selected model - test-model - Version 1 from 2024-09-11T09:13:57Z - was trained/)
        ).toBeInTheDocument();
        expect(screen.queryByText(/12 credits will be deducted./)).not.toBeInTheDocument();
    });
});
