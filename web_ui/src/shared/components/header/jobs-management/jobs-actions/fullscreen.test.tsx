// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

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
