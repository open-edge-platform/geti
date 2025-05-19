// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { useRef } from 'react';

import { defaultTheme, Provider } from '@geti/ui';
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
