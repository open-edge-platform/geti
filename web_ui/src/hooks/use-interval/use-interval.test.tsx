// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { render } from '@testing-library/react';

import { useInterval } from './use-interval.hook';

interface IntervalProps {
    callback: () => void;
    delay: number | null;
}

const Interval = ({ callback, delay }: IntervalProps) => {
    useInterval(callback, delay);

    return null;
};

describe('useInterval', () => {
    afterAll(() => {
        jest.clearAllTimers();
    });

    it('calls the callback on an interval', () => {
        jest.useFakeTimers();

        const callback = jest.fn();
        render(<Interval callback={callback} delay={500} />);

        expect(callback).toBeCalledTimes(0 /* not called on first render */);
        jest.advanceTimersByTime(500);
        expect(callback).toBeCalledTimes(1);
        jest.advanceTimersByTime(1500);
        expect(callback).toBeCalledTimes(4);

        jest.clearAllTimers();
    });
});
