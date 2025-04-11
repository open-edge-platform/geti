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

import { TERMS_OF_USE_GETI } from '../../core/const';
import { useIsSaasEnv } from '../../hooks/use-is-saas-env/use-is-saas-env.hook';
import { providersRender as render } from '../../test-utils/required-providers-render';
import AboutPage from './about-page.component';

jest.mock('../../core/platform-utils/hooks/use-platform-utils.hook', () => ({
    ...jest.requireActual('../../core/platform-utils/hooks/use-platform-utils.hook'),
    usePlatformUtils: jest.fn(() => ({
        useProductInfo: jest.fn(() => ({ data: { productVersion: '1.15.0-test-20240227114821' } })),
    })),
}));

jest.mock('../../hooks/use-is-saas-env/use-is-saas-env.hook', () => ({
    ...jest.requireActual('../../hooks/use-is-saas-env/use-is-saas-env.hook'),
    useIsSaasEnv: jest.fn(() => false),
}));

describe('About page', () => {
    it('Shows build information for OnPrem environments', () => {
        render(<AboutPage />);

        expect(screen.getByText(/1.15.0-test-20240227114821/)).toBeInTheDocument();
    });

    it('Hides build information for Saas environments', () => {
        jest.mocked(useIsSaasEnv).mockReturnValue(true);
        render(<AboutPage />);

        expect(screen.queryByText(/1.15.0-test-20240227114821/)).not.toBeInTheDocument();
    });

    it('Hides terms of use for on-prem environments', () => {
        jest.mocked(useIsSaasEnv).mockReturnValue(false);
        render(<AboutPage />);

        expect(screen.queryByText(/Terms of use & Privacy/)).not.toBeInTheDocument();
    });

    it('Terms of use redirects correctly to the docs page', () => {
        jest.mocked(useIsSaasEnv).mockReturnValue(true);
        render(<AboutPage />);

        const termsOfUseLink = screen.getByText(/Terms of use & Privacy/);

        expect(termsOfUseLink).toHaveAttribute('href', TERMS_OF_USE_GETI);
    });
});
