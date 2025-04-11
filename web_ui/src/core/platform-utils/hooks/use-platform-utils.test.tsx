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

import { ReactNode } from 'react';

import { renderHook, waitFor } from '@testing-library/react';
import { useAuth } from 'react-oidc-context';

import { createInMemoryPlatformUtilsService } from '../services/create-in-memory-platform-utils-service';
import { RequiredProviders } from './../../../test-utils/required-providers-render';
import { usePlatformUtils } from './use-platform-utils.hook';

jest.mock('react-oidc-context', () => ({
    ...jest.requireActual('react-oidc-context'),
    useAuth: jest.fn(() => undefined),
}));

const wrapper = ({ children }: { children?: ReactNode }) => {
    const platformUtilsService = createInMemoryPlatformUtilsService();

    return (
        <RequiredProviders
            platformUtilsService={platformUtilsService}
            featureFlags={{ FEATURE_FLAG_ANALYTICS_WORKFLOW_ID: true }}
        >
            {children}
        </RequiredProviders>
    );
};

describe('useWorkflowId', () => {
    it('Returns the workflowId from based on an authenticated user via OIDC', async () => {
        jest.mocked(useAuth).mockReturnValue({
            user: {
                // @ts-expect-error We only care about the sub value from oidc
                profile: {
                    sub: 'test-workflow-id-from-oidc',
                },
            },
        });

        const { result } = renderHook(() => usePlatformUtils(), { wrapper });
        const { result: workflowId } = renderHook(() => result.current.useWorkflowId(), { wrapper });

        await waitFor(() => {
            expect(workflowId.current.data).toStrictEqual('test-workflow-id-from-oidc');
        });
    });
});

describe('useProductInfo', () => {
    it('Returns the product info from the api', async () => {
        const { result } = renderHook(() => usePlatformUtils(), { wrapper });
        const { result: workflowId } = renderHook(() => result.current.useProductInfo(), { wrapper });

        await waitFor(() => {
            expect(workflowId.current.data).toStrictEqual({
                buildVersion: '1.6.0.test.123123',
                environment: 'on-prem',
                gpuProvider: 'intel',
                grafanaEnabled: false,
                intelEmail: 'support@geti.com',
                isSmtpDefined: true,
                productVersion: '1.6.0',
            });
        });
    });
});
