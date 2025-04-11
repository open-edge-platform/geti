// INTEL CONFIDENTIAL
//
// Copyright (C) 2025 Intel Corporation
//
// This software and the related documents are Intel copyrighted materials, and your use of them is governed by
// the express license under which they were provided to you ("License"). Unless the License provides otherwise,
// you may not use, modify, copy, publish, distribute, disclose or transmit this software or the related documents
// without Intel's prior written permission.
//
// This software and the related documents are provided as is, with no express or implied warranties,
// other than those that are expressly stated in the License.

import { AccountStatus } from '../../core/organizations/organizations.interface';
import { useIsSaasEnv } from '../../hooks/use-is-saas-env/use-is-saas-env.hook';
import { getMockedOrganizationMetadata } from '../../test-utils/mocked-items-factory/mocked-organization';
import { renderHookWithProviders } from '../../test-utils/render-hook-with-providers';
import { useShowRequestAccessConfirmation } from './use-show-request-access-confirmation.hook';

jest.mock('../../hooks/use-is-saas-env/use-is-saas-env.hook', () => ({
    useIsSaasEnv: jest.fn(() => false),
}));

describe('useShowRequestAccessConfirmation', () => {
    it('returns true only when the user is in a SaaS environment, FEATURE_FLAG_USER_ONBOARDING is enabled, FEATURE_FLAG_REQ_ACCESS is enabled, and the user has requested access', () => {
        jest.mocked(useIsSaasEnv).mockReturnValue(true);

        const { result } = renderHookWithProviders(() => useShowRequestAccessConfirmation(), {
            providerProps: {
                profile: {
                    hasAcceptedUserTermsAndConditions: true,
                    organizations: [getMockedOrganizationMetadata({ userStatus: AccountStatus.REQUESTED_ACCESS })],
                },
                featureFlags: {
                    FEATURE_FLAG_USER_ONBOARDING: true,
                    FEATURE_FLAG_REQ_ACCESS: true,
                },
            },
        });

        expect(result.current).toBe(true);
    });

    it('returns false when the user has not requested access', () => {
        jest.mocked(useIsSaasEnv).mockReturnValue(true);

        const { result } = renderHookWithProviders(() => useShowRequestAccessConfirmation(), {
            providerProps: {
                profile: {
                    hasAcceptedUserTermsAndConditions: true,
                    organizations: [getMockedOrganizationMetadata({ userStatus: AccountStatus.ACTIVATED })],
                },
                featureFlags: {
                    FEATURE_FLAG_USER_ONBOARDING: true,
                    FEATURE_FLAG_REQ_ACCESS: true,
                },
            },
        });

        expect(result.current).toBe(false);
    });

    it('returns false when the user is not in a SaaS environment', () => {
        jest.mocked(useIsSaasEnv).mockReturnValue(false);

        const { result } = renderHookWithProviders(() => useShowRequestAccessConfirmation(), {
            providerProps: {
                profile: {
                    hasAcceptedUserTermsAndConditions: true,
                    organizations: [getMockedOrganizationMetadata({ userStatus: AccountStatus.REQUESTED_ACCESS })],
                },
                featureFlags: {
                    FEATURE_FLAG_USER_ONBOARDING: true,
                    FEATURE_FLAG_REQ_ACCESS: true,
                },
            },
        });

        expect(result.current).toBe(false);
    });

    it('returns false when the FEATURE_FLAG_USER_ONBOARDING is disabled', () => {
        jest.mocked(useIsSaasEnv).mockReturnValue(true);

        const { result } = renderHookWithProviders(() => useShowRequestAccessConfirmation(), {
            providerProps: {
                profile: {
                    hasAcceptedUserTermsAndConditions: true,
                    organizations: [getMockedOrganizationMetadata({ userStatus: AccountStatus.REQUESTED_ACCESS })],
                },
                featureFlags: {
                    FEATURE_FLAG_USER_ONBOARDING: false,
                    FEATURE_FLAG_REQ_ACCESS: true,
                },
            },
        });

        expect(result.current).toBe(false);
    });

    it('returns false when FEATURE_FLAG_REQ_ACCESS is disabled', () => {
        jest.mocked(useIsSaasEnv).mockReturnValue(true);

        const { result } = renderHookWithProviders(() => useShowRequestAccessConfirmation(), {
            providerProps: {
                profile: {
                    hasAcceptedUserTermsAndConditions: true,
                    organizations: [getMockedOrganizationMetadata({ userStatus: AccountStatus.REQUESTED_ACCESS })],
                },
                featureFlags: {
                    FEATURE_FLAG_USER_ONBOARDING: true,
                    FEATURE_FLAG_REQ_ACCESS: false,
                },
            },
        });

        expect(result.current).toBe(false);
    });
});
