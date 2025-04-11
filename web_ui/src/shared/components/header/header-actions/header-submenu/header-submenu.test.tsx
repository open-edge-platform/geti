// INTEL CONFIDENTIAL
//
// Copyright (C) 2022 Intel Corporation
//
// This software and the related documents are Intel copyrighted materials, and your use of them is governed by
// the express license under which they were provided to you ("License"). Unless the License provides otherwise,
// you may not use, modify, copy, publish, distribute, disclose or transmit this software or the related documents
// without Intel's prior written permission.
//
// This software and the related documents are provided as is, with no express or implied warranties,
// other than those that are expressly stated in the License.

import { Key } from 'react';

import { fireEvent, screen } from '@testing-library/react';

import { providersRender as render } from '../../../../../test-utils/required-providers-render';
import { HeaderSubmenu } from './header-submenu.component';

describe('HeaderSubmenu', () => {
    const mockedItemsText = ['Mocked item 1', 'Mocked item 2', 'Mocked item 3'];
    const mockedHandlers = [jest.fn(), jest.fn(), jest.fn()];
    const mockedItems = [
        {
            children: [
                {
                    text: mockedItemsText[0],
                    id: 'test1-id',
                },
                {
                    text: mockedItemsText[1],
                    id: 'test2-id',
                },
                {
                    text: mockedItemsText[2],
                    id: 'test3-id',
                },
            ],
            id: 'test-id',
        },
    ];

    const handleMenuAction = (key: Key): void => {
        const items = mockedItems[0].children;
        switch (key) {
            case items[0].id:
                mockedHandlers[0]();
                break;
            case items[1].id:
                mockedHandlers[1]();
                break;
            case items[2].id:
                mockedHandlers[2]();
                break;
            default:
                return;
        }
    };

    const renderHeaderSubmenu = async (isDarkMode = false): Promise<void> => {
        await render(
            <HeaderSubmenu
                items={mockedItems}
                icon={<></>}
                ariaLabel={'test-label'}
                onMenuAction={handleMenuAction}
                isDarkMode={isDarkMode}
            />
        );
    };

    it('All submenu items should be visible', async () => {
        await renderHeaderSubmenu();

        fireEvent.click(screen.getByRole('button', { name: 'test-label' }));

        mockedItemsText.forEach((item) => {
            expect(screen.getByText(item)).toBeInTheDocument();
        });
    });

    it("Item's handler should be called properly", async () => {
        await renderHeaderSubmenu();

        fireEvent.click(screen.getByRole('button', { name: 'test-label' }));

        mockedItemsText.forEach((item, index) => {
            fireEvent.click(screen.getByText(item));

            expect(mockedHandlers[index]).toHaveBeenCalled();

            fireEvent.click(screen.getByRole('button', { name: 'test-label' }));
        });
    });

    it('Button should have light styles if isDarkMode is false', async () => {
        await renderHeaderSubmenu();

        expect(screen.getByRole('button', { name: 'test-label' })).toHaveClass('actionButtonLight', { exact: false });
    });

    it('Button should have light styles if isDarkBackground is true', async () => {
        await renderHeaderSubmenu(true);

        expect(screen.getByRole('button', { name: 'test-label' })).toHaveClass('actionButtonDark', { exact: false });
    });
});
