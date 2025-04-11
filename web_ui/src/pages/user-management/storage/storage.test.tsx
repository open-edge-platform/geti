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

import { screen, waitForElementToBeRemoved } from '@testing-library/react';

import { providersRender as render } from '../../../test-utils/required-providers-render';
import { Storage } from './storage.component';

jest.mock('react-router-dom', () => ({
    ...jest.requireActual('react-router-dom'),
    useParams: () => ({
        organizationId: 'organization-id',
        workspaceId: 'workspace_1',
    }),
}));

const renderStorage = ({
    FEATURE_FLAG_STORAGE_SIZE_COMPUTATION,
}: {
    FEATURE_FLAG_STORAGE_SIZE_COMPUTATION: boolean;
}) => {
    render(<Storage />, { featureFlags: { FEATURE_FLAG_STORAGE_SIZE_COMPUTATION } });
};

describe('Storage', () => {
    it('storage usage should not be visible when FEATURE_FLAG_STORAGE_SIZE_COMPUTATION is false', async () => {
        renderStorage({ FEATURE_FLAG_STORAGE_SIZE_COMPUTATION: false });

        expect(screen.queryByRole('heading', { name: 'Storage usage' })).not.toBeInTheDocument();
    });

    it('storage usage should not be visible when FEATURE_FLAG_STORAGE_SIZE_COMPUTATION is true', async () => {
        renderStorage({ FEATURE_FLAG_STORAGE_SIZE_COMPUTATION: true });

        await waitForElementToBeRemoved(screen.getByTestId('storage-usage-loading-id'));

        expect(screen.getByRole('heading', { name: 'Storage usage' })).toBeInTheDocument();
    });

    it('should render the projects storage', async () => {
        renderStorage({ FEATURE_FLAG_STORAGE_SIZE_COMPUTATION: true });

        expect(screen.getByRole('heading', { name: 'Usage per project' })).toBeInTheDocument();
    });
});
