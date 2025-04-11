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

import { renderHook } from '@testing-library/react';

import { useDeploymentConfigQuery } from '../../core/services/use-deployment-config-query.hook';
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
jest.mock('../../core/services/use-deployment-config-query.hook', () => ({
    ...jest.requireActual('../../core/services/use-deployment-config-query.hook'),
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
            data: { ...mockConfig, servingMode: 'saas', docsUrl: 'https://docs.geti.intel.com/cloud/' },
        });

        const { result } = renderHook(() => useIsSaasEnv());

        expect(result.current).toBe(true);
    });
});
