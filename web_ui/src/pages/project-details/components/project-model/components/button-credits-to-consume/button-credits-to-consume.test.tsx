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
