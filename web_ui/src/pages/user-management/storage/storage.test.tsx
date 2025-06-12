// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

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

        await waitForElementToBeRemoved(screen.getByLabelText('Loading...'));

        expect(screen.getByRole('heading', { name: 'Storage usage' })).toBeInTheDocument();
    });

    it('should render the projects storage', async () => {
        renderStorage({ FEATURE_FLAG_STORAGE_SIZE_COMPUTATION: true });

        expect(screen.getByRole('heading', { name: 'Usage per project' })).toBeInTheDocument();
    });
});
