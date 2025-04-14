// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { screen } from '@testing-library/react';

import { projectRender } from '../../../../../../test-utils/project-provider-render';
import { ButtonCreditsToConsume } from './button-credits-to-consume.component';

describe('ButtonCreditsToConsume', () => {
    const renderApp = async ({ creditFlag = false, loading = false }: { creditFlag?: boolean; loading?: boolean }) => {
        return projectRender(
            <ButtonCreditsToConsume taskId={''} isLoading={loading} getTooltip={() => 'test tooltip'} />,
            {
                featureFlags: { FEATURE_FLAG_CREDIT_SYSTEM: creditFlag },
            }
        );
    };

    it('render credit totals', async () => {
        await renderApp({ loading: false, creditFlag: true });

        expect(await screen.findByText(`Train (7 credits)`)).toBeVisible();
    });

    it('credit flag is off', async () => {
        await renderApp({ loading: false, creditFlag: false });

        expect(screen.getByText(`Start`)).toBeVisible();
    });
});
