// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import '@wessberg/pointer-events';

import { fireEvent, screen, waitFor } from '@testing-library/react';
import { useSearchParams } from 'react-router-dom';

import { delay } from '../../../../shared/utils';
import { projectRender as render } from '../../../../test-utils/project-provider-render';
import { CaptureButtonAnimation, MOUSE_HOLD_TIMER } from './capture-button-animation.component';

jest.mock('react-router-dom', () => ({
    ...jest.requireActual('react-router-dom'),
    useSearchParams: jest.fn(),
}));

const pressHoldButton = async (videoTag: HTMLVideoElement, time = MOUSE_HOLD_TIMER) => {
    const animationEndEvent = new Event('animationend');

    fireEvent.pointerDown(screen.getByRole('button', { name: /photo capture/i }));
    Object.assign(animationEndEvent, { animationName: 'oldCameraAnimation' });
    fireEvent(videoTag, animationEndEvent);

    // Wait MOUSE_HOLD_TIMER ms's to start burst mode
    await delay(MOUSE_HOLD_TIMER);

    await delay(time);

    fireEvent.pointerUp(screen.getByRole('button', { name: /photo capture/i }));
    Object.assign(animationEndEvent, { animationName: 'flashAnimation' });
    fireEvent(videoTag, animationEndEvent);
};

describe('CaptureButtonAnimation', () => {
    const renderApp = async ({ onPress = jest.fn() }: { onPress?: jest.Mock }) => {
        const videoTag = document.createElement('video');
        const searchParams = new URLSearchParams();

        jest.mocked(useSearchParams).mockImplementation(() => [searchParams, jest.fn()]);

        await render(<CaptureButtonAnimation onPress={onPress} videoTag={videoTag} />);

        return videoTag;
    };

    it('video tag get animation class', async () => {
        const mockedVideoTag = await renderApp({});

        fireEvent.click(screen.getByRole('button', { name: /photo capture/i }));

        expect(mockedVideoTag).toHaveClass('takeOldCamera');
    });

    it('user click calls onPress once', async () => {
        const animationEndEvent = new Event('animationend');
        Object.assign(animationEndEvent, { animationName: 'oldCameraAnimation' });

        const mockedPress = jest.fn();
        const mockedVideoTag = await renderApp({ onPress: mockedPress });

        fireEvent.click(screen.getByRole('button', { name: /photo capture/i }));

        fireEvent(mockedVideoTag, animationEndEvent);

        expect(mockedPress).toHaveBeenCalledTimes(1);
    });

    it('user holds button pressed, onPress get called multiple times (burst mode)', async () => {
        const mockedPress = jest.fn();
        const mockedVideoTag = await renderApp({ onPress: mockedPress });

        // Wait for MOUSE_HOLD_TIMER for the setInterval to start
        // Wait for extra MOUSE_HOLD_TIMER to execute the callback 10 times
        await pressHoldButton(mockedVideoTag, MOUSE_HOLD_TIMER + 50);

        await waitFor(() => {
            expect(mockedPress.mock.calls.length).toBeGreaterThanOrEqual(10);
        });
    });
});
