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

import { fireEvent, screen } from '@testing-library/react';

import { providersRender as render } from '../../../../test-utils/required-providers-render';
import { JobsDialog } from './jobs-dialog.component';

jest.mock('react-router-dom', () => ({
    ...jest.requireActual('react-router-dom'),
    useParams: () => ({
        organizationId: 'organization-id',
        workspaceId: 'workspace_1',
    }),
}));

describe('jobs dialog', (): void => {
    beforeEach((): void => {
        jest.clearAllMocks();
    });

    const renderComponent = () => {
        render(<JobsDialog onClose={jest.fn()} isFullScreen={false} setIsFullScreen={jest.fn()} />);
    };

    it('should properly render job management dialog', async (): Promise<void> => {
        renderComponent();

        expect(screen.getByRole('dialog')).toBeVisible();

        expect(screen.getByLabelText('Job scheduler filter project')).toBeInTheDocument();
        expect(screen.getByLabelText('Job scheduler filter user')).toBeInTheDocument();
        expect(screen.getByLabelText('Job scheduler filter job type')).toBeInTheDocument();

        expect(screen.getByRole('tablist', { name: 'Job management tabs' })).toBeInTheDocument();

        expect(screen.getByRole('tab', { name: 'Running jobs' })).toBeInTheDocument();
        expect(screen.getByRole('tab', { name: 'Running jobs' })).toHaveAttribute('aria-selected', 'true');

        expect(screen.getByRole('tab', { name: 'Finished jobs' })).toBeInTheDocument();
        expect(screen.getByRole('tab', { name: 'Scheduled jobs' })).toBeInTheDocument();
        expect(screen.getByRole('tab', { name: 'Cancelled jobs' })).toBeInTheDocument();
        expect(screen.getByRole('tab', { name: 'Failed jobs' })).toBeInTheDocument();
    });

    it('should properly switch between job management tabs', async (): Promise<void> => {
        renderComponent();

        expect(screen.getByRole('tab', { name: 'Running jobs' })).toBeInTheDocument();
        expect(screen.getByRole('tab', { name: 'Finished jobs' })).toBeInTheDocument();
        expect(screen.getByRole('tab', { name: 'Scheduled jobs' })).toBeInTheDocument();
        expect(screen.getByRole('tab', { name: 'Cancelled jobs' })).toBeInTheDocument();
        expect(screen.getByRole('tab', { name: 'Failed jobs' })).toBeInTheDocument();

        expect(screen.getByRole('tab', { name: 'Running jobs' })).toHaveAttribute('aria-selected', 'true');

        fireEvent.click(screen.getByRole('tab', { name: 'Finished jobs' }));
        expect(screen.getByRole('tab', { name: 'Running jobs' })).toHaveAttribute('aria-selected', 'false');
        expect(screen.getByRole('tab', { name: 'Finished jobs' })).toHaveAttribute('aria-selected', 'true');

        fireEvent.click(screen.getByRole('tab', { name: 'Scheduled jobs' }));
        expect(screen.getByRole('tab', { name: 'Running jobs' })).toHaveAttribute('aria-selected', 'false');
        expect(screen.getByRole('tab', { name: 'Finished jobs' })).toHaveAttribute('aria-selected', 'false');
        expect(screen.getByRole('tab', { name: 'Scheduled jobs' })).toHaveAttribute('aria-selected', 'true');

        fireEvent.click(screen.getByRole('tab', { name: 'Cancelled jobs' }));
        expect(screen.getByRole('tab', { name: 'Running jobs' })).toHaveAttribute('aria-selected', 'false');
        expect(screen.getByRole('tab', { name: 'Finished jobs' })).toHaveAttribute('aria-selected', 'false');
        expect(screen.getByRole('tab', { name: 'Scheduled jobs' })).toHaveAttribute('aria-selected', 'false');
        expect(screen.getByRole('tab', { name: 'Cancelled jobs' })).toHaveAttribute('aria-selected', 'true');

        fireEvent.click(screen.getByRole('tab', { name: 'Failed jobs' }));
        expect(screen.getByRole('tab', { name: 'Running jobs' })).toHaveAttribute('aria-selected', 'false');
        expect(screen.getByRole('tab', { name: 'Finished jobs' })).toHaveAttribute('aria-selected', 'false');
        expect(screen.getByRole('tab', { name: 'Scheduled jobs' })).toHaveAttribute('aria-selected', 'false');
        expect(screen.getByRole('tab', { name: 'Cancelled jobs' })).toHaveAttribute('aria-selected', 'false');
        expect(screen.getByRole('tab', { name: 'Failed jobs' })).toHaveAttribute('aria-selected', 'true');
    });
});
