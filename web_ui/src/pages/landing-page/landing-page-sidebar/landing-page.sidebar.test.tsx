// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { paths } from '@geti/core';
import { screen, waitForElementToBeRemoved, within } from '@testing-library/react';

import { providersRender } from '../../../test-utils/required-providers-render';
import { LandingPageSidebar } from './landing-page-sidebar.component';

const mockedNavigate = jest.fn();
jest.mock('react-router-dom', () => ({
    ...jest.requireActual('react-router-dom'),
    useNavigate: () => mockedNavigate,
    useParams: jest.fn(() => ({ organizationId: 'organization-id', workspaceId: 'workspace-id' })),
}));

describe('Landing page - sidebar', () => {
    it('Check if there are 3 options in sidebar menu - Projects, Account, About', async () => {
        providersRender(<LandingPageSidebar />);
        await waitForElementToBeRemoved(screen.getByRole('progressbar'));
        const options = within(screen.getByRole('navigation')).getAllByRole('link');

        expect(options).toHaveLength(3);
        expect(options.map((element: HTMLElement) => element.textContent)).toEqual(
            expect.arrayContaining([
                expect.stringContaining('Projects'),
                expect.stringContaining('Account'),
                expect.stringContaining('About'),
            ])
        );
    });

    it('Should should show terms of use and privacy', async () => {
        providersRender(<LandingPageSidebar />);
        await waitForElementToBeRemoved(screen.getByRole('progressbar'));

        expect(screen.getByText(/Terms of use/)).toBeInTheDocument();
        expect(screen.getByText(/Privacy/)).toBeInTheDocument();

        expect(
            screen.getByRole('link', {
                name: /terms of use privacy/i,
            })
        ).toHaveAttribute('href', paths.organization.about({ organizationId: 'organization-id' }));
    });
});
