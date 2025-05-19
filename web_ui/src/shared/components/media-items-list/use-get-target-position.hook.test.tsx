// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { renderHook } from '@testing-library/react';

import { useGetTargetPosition } from './use-get-target-position.hook';

describe('useGetTargetPosition', () => {
    const mockCallback = jest.fn();

    beforeEach(() => {
        jest.useFakeTimers();
        jest.clearAllMocks();
        jest.clearAllTimers();
    });

    afterEach(() => {
        jest.useRealTimers();
    });

    it('should not call callback when container is not provided', () => {
        renderHook(() =>
            useGetTargetPosition({
                gap: 10,
                container: null,
                targetIndex: 5,
                callback: mockCallback,
            })
        );

        jest.advanceTimersByTime(500);

        expect(mockCallback).not.toHaveBeenCalled();
    });

    it('calls callback with correct scroll position', () => {
        const gap = 0;
        const childWidth = 100;
        const childHeight = 100;
        const targetIndex = 12;
        const containerWidth = 200;

        const container = document.createElement('div');
        Object.defineProperty(container, 'clientWidth', { value: containerWidth });

        const child = document.createElement('div');
        Object.defineProperty(child, 'clientWidth', { value: childWidth });
        Object.defineProperty(child, 'clientHeight', { value: childHeight });

        container.appendChild(child);

        const itemsPerRow = Math.floor(containerWidth / childWidth); // 2
        const targetRow = Math.floor(targetIndex / itemsPerRow); // 6
        const expectedScrollPos = (childHeight + gap) * targetRow; // 600

        renderHook(() =>
            useGetTargetPosition({
                gap,
                container,
                targetIndex,
                callback: mockCallback,
            })
        );

        jest.advanceTimersByTime(500);

        expect(mockCallback).toHaveBeenCalledWith(expectedScrollPos);
    });

    it('return zero when container has no children', () => {
        const container = document.createElement('div');
        Object.defineProperty(container, 'clientWidth', { value: 1000 });

        renderHook(() =>
            useGetTargetPosition({
                gap: 10,
                container,
                targetIndex: 5,
                callback: mockCallback,
            })
        );

        jest.advanceTimersByTime(500);

        expect(mockCallback).toHaveBeenCalledWith(0);
    });

    describe('should not call callback with invalid index', () => {
        it.each([undefined, null, -1, 1.5, NaN])('targetIndex: %p', (invalidIndex) => {
            renderHook(() =>
                useGetTargetPosition({
                    gap: 10,
                    container: document.createElement('div'),
                    targetIndex: invalidIndex as number,
                    callback: mockCallback,
                })
            );

            jest.advanceTimersByTime(500);

            expect(mockCallback).not.toHaveBeenCalled();
        });
    });
});
