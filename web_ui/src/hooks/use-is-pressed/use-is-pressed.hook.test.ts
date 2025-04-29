// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { fireEvent, waitFor } from '@testing-library/react';

import { KeyMap } from '../../shared/keyboard-events/keyboard.interface';
import { renderHook } from '../../test-utils/render-hook';
import { useIsPressed } from './use-is-pressed.hook';

describe('useIsPressed', () => {
    const deleteKeyConfig = { key: 'Delete', code: 'Delete', keyCode: 46 };

    it('return false when the key is released', async () => {
        const { result } = renderHook(() => useIsPressed({ key: KeyMap.Delete }));

        fireEvent.keyDown(document.body, deleteKeyConfig);

        await waitFor(() => {
            expect(result.current).toBe(true);
        });

        fireEvent.keyUp(document.body, deleteKeyConfig);

        await waitFor(() => {
            expect(result.current).toBe(false);
        });
    });

    it('not set isPressed if keyDownPredicated returns false', async () => {
        const mockedPredicated = jest.fn().mockReturnValue(false);
        const { result } = renderHook(() => useIsPressed({ key: KeyMap.Delete, predicated: mockedPredicated }));

        fireEvent.keyDown(document.body, deleteKeyConfig);

        await waitFor(() => {
            expect(result.current).toBe(false);
            expect(mockedPredicated).toHaveBeenCalled();
        });
    });

    describe('callback calling', () => {
        it('key is pressed', async () => {
            const onKeyDown = jest.fn();
            renderHook(() => useIsPressed({ key: KeyMap.Delete, onKeyDown }));

            fireEvent.keyDown(document.body, deleteKeyConfig);

            expect(onKeyDown).toHaveBeenCalled();
        });

        it('key is released', async () => {
            const onKeyUp = jest.fn();
            renderHook(() => useIsPressed({ key: KeyMap.Delete, onKeyUp }));

            fireEvent.keyDown(document.body, deleteKeyConfig);
            fireEvent.keyUp(document.body, deleteKeyConfig);

            expect(onKeyUp).toHaveBeenCalled();
        });
    });
});
