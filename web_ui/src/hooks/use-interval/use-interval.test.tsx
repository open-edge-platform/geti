// INTEL CONFIDENTIAL
//
// Copyright (C) 2021 Intel Corporation
//
// This software and the related documents are Intel copyrighted materials, and your use of them is governed by
// the express license under which they were provided to you ("License"). Unless the License provides otherwise,
// you may not use, modify, copy, publish, distribute, disclose or transmit this software or the related documents
// without Intel's prior written permission.
//
// This software and the related documents are provided as is, with no express or implied warranties,
// other than those that are expressly stated in the License.

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
