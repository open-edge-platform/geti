// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { useDeploymentConfigQuery } from '@geti/core/src/services/use-deployment-config-query.hook';
import { renderHook } from '@testing-library/react';

import { useIsSaasEnv } from './use-is-saas-env.hook';

const mockConfig = {
    servingMode: 'on-prem',
    auth: {
        type: 'dex',
        clientId: 'web_ui',
        authority: '/dex',
    },
    controlPlaneUrl: null,
    dataPlaneUrl: null,
    docsUrl: 'https://docs.geti.intel.com/on-prem/2.6/',
};
jest.mock('@geti/core/src/services/use-deployment-config-query.hook', () => ({
    ...jest.requireActual('@geti/core/src/services/use-deployment-config-query.hook'),
    useDeploymentConfigQuery: jest.fn(() => ({
        data: mockConfig,
    })),
}));

describe('useIsSaasEnv', () => {
    it('returns false if environment is onPrem', () => {
        // @ts-expect-error We only use data
        jest.mocked(useDeploymentConfigQuery).mockReturnValue({ data: mockConfig });

        const { result } = renderHook(() => useIsSaasEnv());

        expect(result.current).toBe(false);
    });

    it('returns true if environment is Saas', () => {
        jest.mocked(useDeploymentConfigQuery).mockReturnValue({
            // @ts-expect-error We only use data
            data: { ...mockConfig, servingMode: 'saas', docsUrl: 'https://docs.geti.intel.com/' },
        });

        const { result } = renderHook(() => useIsSaasEnv());

        expect(result.current).toBe(true);
    });
});
