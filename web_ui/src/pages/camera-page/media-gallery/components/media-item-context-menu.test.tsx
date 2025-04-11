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

import { useRef } from 'react';

import { defaultTheme, Provider } from '@adobe/react-spectrum';
import { render, screen } from '@testing-library/react';
import { userEvent } from '@testing-library/user-event';

import { MediaItemContextMenu } from './media-item-context-menu.component';

const App = (props: { options: [string, () => void][] }) => {
    const ref = useRef(null);

    return (
        <div aria-label={'menu container'} ref={ref}>
            <MediaItemContextMenu {...props} containerRef={ref} />;
        </div>
    );
};
describe('MediaItemContextMenu', () => {
    const user = userEvent.setup({ advanceTimers: jest.advanceTimersByTime });

    beforeAll(() => {
        jest.useFakeTimers();
    });

    afterAll(() => {
        jest.useRealTimers();
        jest.clearAllTimers();
    });

    it('context menu button is hidden', async () => {
        render(
            <Provider theme={defaultTheme}>
                <App options={[['Delete', jest.fn()]]} />
            </Provider>
        );

        expect(screen.getByLabelText('context menu')).not.toBeVisible();
    });

    it('calls option action', async () => {
        const mockedDeleteAction = jest.fn();

        render(
            <Provider theme={defaultTheme}>
                <App options={[['Delete', mockedDeleteAction]]} />
            </Provider>
        );

        await user.pointer({ keys: '[MouseRight>]', target: screen.getByLabelText('menu container') });
        jest.advanceTimersByTime(1000);
        await user.click(screen.getByLabelText('Delete'));

        expect(mockedDeleteAction).toHaveBeenCalledTimes(1);
    });
});
