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

import { useIsSaasEnv } from '../../../hooks/use-is-saas-env/use-is-saas-env.hook';
import { providersRender as render } from '../../../test-utils/required-providers-render';
import { usePreviousSignIn } from '../../hooks/use-previous-sign-in.hook';
import { LastLoginNotification } from './last-login-notification';

jest.mock('../../../hooks/use-is-saas-env/use-is-saas-env.hook', () => ({
    ...jest.requireActual('../../../hooks/use-is-saas-env/use-is-saas-env.hook'),
    useIsSaasEnv: jest.fn(),
}));

jest.mock('../../hooks/use-previous-sign-in.hook', () => ({
    ...jest.requireActual('../../hooks/use-previous-sign-in.hook'),
    usePreviousSignIn: jest.fn(() => ({ lastLoginDate: null, userId: '' })),
}));

describe('LastLoginNotification', () => {
    beforeEach(() => {
        jest.clearAllMocks();
    });

    describe('should show notification', () => {
        it('for SaaS environments and if lastLoginDate is not "null"', async () => {
            jest.mocked(useIsSaasEnv).mockReturnValue(true);
            jest.mocked(usePreviousSignIn).mockReturnValue({ lastLoginDate: '19 july 2024', userId: 'some-id' });
            await render(<LastLoginNotification />);

            expect(screen.getByText(/Your previous sign-in/)).toBeInTheDocument();
        });
    });

    describe('should NOT show notification', () => {
        it('for onprem environments', async () => {
            jest.mocked(useIsSaasEnv).mockReturnValueOnce(false);

            await render(<LastLoginNotification />);

            expect(screen.queryByText(/Your previous sign-in/)).not.toBeInTheDocument();
        });

        it('if lastLoginDate is "null"', async () => {
            jest.mocked(useIsSaasEnv).mockReturnValueOnce(true);
            jest.mocked(usePreviousSignIn).mockReturnValueOnce({ lastLoginDate: null, userId: undefined });

            await render(<LastLoginNotification />);

            expect(screen.queryByText(/Your previous sign-in/)).not.toBeInTheDocument();
        });
    });
});
