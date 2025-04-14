// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { screen, within } from '@testing-library/react';

import { paths } from '../../../core/services/routes';
import { providersRender } from '../../../test-utils/required-providers-render';
import { LandingPageSidebar } from './landing-page-sidebar.component';

const mockedNavigate = jest.fn();
jest.mock('react-router-dom', () => ({
    ...jest.requireActual('react-router-dom'),
    useNavigate: () => mockedNavigate,
    useParams: jest.fn(() => ({ organizationId: 'organization-id', workspaceId: 'workspace-id' })),
}));

describe('Landing page - sidebar', () => {
    it('Check if there are 4 options in sidebar menu - Projects, Account, Learn, About', async () => {
        providersRender(<LandingPageSidebar />);
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

        expect(screen.getByText(/Terms of use/)).toBeInTheDocument();
        expect(screen.getByText(/Privacy/)).toBeInTheDocument();

        expect(
            screen.getByRole('link', {
                name: /terms of use privacy/i,
            })
        ).toHaveAttribute('href', paths.organization.about({ organizationId: 'organization-id' }));
    });
});
