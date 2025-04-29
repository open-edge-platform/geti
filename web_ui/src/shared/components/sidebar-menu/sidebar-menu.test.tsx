// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { render, screen } from '@testing-library/react';
import { MemoryRouter as Router } from 'react-router-dom';

import { getById } from '../../../test-utils/utils';
import { MenuOption } from '../menu-option.interface';
import { SidebarMenu } from './sidebar-menu.component';

describe('Sidebar menu', () => {
    const options: MenuOption[][] = [
        [
            {
                id: 'test1',
                name: 'Test 1',
                url: '/sidebar-menu/test1',
                ariaLabel: 'side bar menu test 1',
            },
            {
                id: 'test2',
                name: 'Test 2',
                url: '/sidebar-menu/test2',
                ariaLabel: 'side bar menu test 2',
            },
        ],
        [
            {
                id: 'test3',
                name: 'Test 3',
                url: '/sidebar-menu/test3',
                ariaLabel: 'side bar menu test 3',
            },
            {
                id: 'test4',
                name: 'Test 4',
                url: '/sidebar-menu/test4',
                ariaLabel: 'side bar menu test 4',
            },
        ],
    ];

    const App = () => (
        <Router initialEntries={['/sidebar-menu/test2']}>
            <SidebarMenu options={options} id='test' />
        </Router>
    );

    it('Check if there are proper options displayed', () => {
        const { container } = render(<App />);

        expect(screen.getByRole('navigation')).toBeInTheDocument();

        // Each group of links is put inside of a group and separated by a separator
        expect(screen.getAllByRole('list', { name: 'list group' })).toHaveLength(options.length);
        expect(screen.getAllByRole('separator')).toHaveLength(options.length - 1);

        // Check that we render the expected links
        expect(getById(container, 'sidebar-menu-test1')).toBeInTheDocument();
        expect(getById(container, 'sidebar-menu-test2')).toBeInTheDocument();

        expect(screen.getAllByRole('link')).toHaveLength(4);

        const link1 = screen.getByRole('link', { name: 'Test 1' });
        expect(link1).toHaveAttribute('href', options[0][0].url);
        expect(link1).not.toHaveAttribute('aria-current', 'page');
        expect(screen.getByRole('listitem', { name: options[0][0].ariaLabel })).toBeInTheDocument();

        const link2 = screen.getByRole('link', { name: 'Test 2' });
        expect(link2).toHaveAttribute('href', options[0][1].url);
        expect(link2).toHaveAttribute('aria-current', 'page');
    });
});
