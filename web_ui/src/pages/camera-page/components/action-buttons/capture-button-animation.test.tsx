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
    const renderApp = async ({
        onPress = jest.fn(),
        isLivePrediction = 'false',
    }: {
        onPress?: jest.Mock;

        isLivePrediction?: 'false' | 'true';
    }) => {
        const videoTag = document.createElement('video');
        const searchParams = new URLSearchParams();

        searchParams.set('isLivePrediction', isLivePrediction);
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

    it('burst mode is disabled on uniqueScreenshot mode', async () => {
        const mockedPress = jest.fn();
        const mockedVideoTag = await renderApp({ onPress: mockedPress, isLivePrediction: 'true' });

        await pressHoldButton(mockedVideoTag);

        expect(mockedPress).toHaveBeenCalledTimes(1);
    });
});
