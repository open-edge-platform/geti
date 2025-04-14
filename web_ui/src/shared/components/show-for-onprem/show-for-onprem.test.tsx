// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

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
