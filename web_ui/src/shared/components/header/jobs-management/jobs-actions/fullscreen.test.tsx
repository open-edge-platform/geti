// INTEL CONFIDENTIAL
//
// Copyright (C) 2023 Intel Corporation
//
// This software and the related documents are Intel copyrighted materials, and your use of them is governed by
// the express license under which they were provided to you ("License"). Unless the License provides otherwise,
// you may not use, modify, copy, publish, distribute, disclose or transmit this software or the related documents
// without Intel's prior written permission.
//
// This software and the related documents are provided as is, with no express or implied warranties,
// other than those that are expressly stated in the License.

import { fireEvent, render, screen } from '@testing-library/react';

import { Fullscreen } from './fullscreen.component';

describe('job scheduler fullscreen', (): void => {
    it('should properly render collapse icon', (): void => {
        render(<Fullscreen enabled toggle={jest.fn()} />);
        expect(screen.getByText('collapse.svg')).toBeInTheDocument();
        expect(screen.queryByText('expand.svg')).not.toBeInTheDocument();
    });

    it('should properly render expand icon', (): void => {
        render(<Fullscreen enabled={false} toggle={jest.fn()} />);
        expect(screen.getByText('expand.svg')).toBeInTheDocument();
        expect(screen.queryByText('collapse.svg')).not.toBeInTheDocument();
    });

    it('should trigger toggle callback on press event', (): void => {
        const onToggle = jest.fn((innerFunction) => {
            expect(innerFunction(true)).toBe(false);
            expect(innerFunction(false)).toBe(true);
        });

        render(<Fullscreen enabled toggle={onToggle} />);
        fireEvent.click(screen.getByTestId('job-scheduler-action-expand'));
        expect(onToggle).toBeCalledWith(expect.any(Function));
    });
});
