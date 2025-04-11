// INTEL CONFIDENTIAL
//
// Copyright (C) 2023 Intel Corporation
//
// This software and the related documents are Intel copyrighted materials, and your use of them is governed by
// the express license under which they were provided to you ("License"). Unless the License provides otherwise,
// you may not use, modify, copy, publish, distribute, disclose or transmit this software or the related documents
// without Intel's prior written permission.
//
// This software and the related documents are provided as is, with no express or implied warranties,
// other than those that are expressly stated in the License.

import { render, screen } from '@testing-library/react';

import { useIsSaasEnv } from '../../../hooks/use-is-saas-env/use-is-saas-env.hook';
import { ShowForOnPrem } from './show-for-onprem.component';

jest.mock('../../../hooks/use-is-saas-env/use-is-saas-env.hook', () => ({
    ...jest.requireActual('../../../hooks/use-is-saas-env/use-is-saas-env.hook'),
    useIsSaasEnv: jest.fn(() => false),
}));

describe('Show/hide for onPrem or Saas', () => {
    it('ShowForOnPrem should not show content when env is SaaS', () => {
        jest.mocked(useIsSaasEnv).mockImplementation(() => true);

        render(
            <ShowForOnPrem>
                <p>Content</p>
            </ShowForOnPrem>
        );

        expect(screen.queryByText('Content')).not.toBeInTheDocument();
    });

    it('ShowForOnPrem should show content when env is on prem', () => {
        jest.mocked(useIsSaasEnv).mockImplementation(() => false);

        render(
            <ShowForOnPrem>
                <p>Content</p>
            </ShowForOnPrem>
        );

        expect(screen.getByText('Content')).toBeInTheDocument();
    });
});
