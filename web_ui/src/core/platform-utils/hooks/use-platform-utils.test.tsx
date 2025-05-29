// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { ReactNode } from 'react';

import { renderHook, waitFor } from '@testing-library/react';
import { useAuth } from 'react-oidc-context';

import { createInMemoryPlatformUtilsService } from '../services/create-in-memory-platform-utils-service';
import { RequiredProviders } from './../../../test-utils/required-providers-render';
import { useProductInfo, useWorkflowId } from './use-platform-utils.hook';

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

        const { result: workflowId } = renderHook(() => useWorkflowId(), { wrapper });

        await waitFor(() => {
            expect(workflowId.current.data).toStrictEqual('test-workflow-id-from-oidc');
        });
    });
});

describe('useProductInfo', () => {
    it('Returns the product info from the api', async () => {
        const { result } = renderHook(() => useProductInfo(), { wrapper });

        await waitFor(() => {
            expect(result.current.data).toStrictEqual({
                buildVersion: '1.6.0.test.123123',
                environment: 'on-prem',
                gpuProvider: 'intel',
                grafanaEnabled: false,
                intelEmail: 'support@geti.com',
                isSmtpDefined: true,
                productVersion: '1.6.0',
                installationMode: 'standard',
            });
        });
    });
});
