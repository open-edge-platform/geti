// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { fireEvent, screen } from '@testing-library/react';

import { providersRender as render } from '../../../../test-utils/required-providers-render';
import { MediaFilterValueShapeAreaPercentage } from './media-filter-value-shape-area-percentage.component';

jest.mock('lodash-es/debounce', () => (callback: (t: string) => void) => (value: string) => callback(value));

describe('MediaFilterValueLabel', () => {
    const onSelectionChange = jest.fn();
    const getInput = (): HTMLTextAreaElement =>
        screen.getByLabelText('media-filter-shape-area-percentage') as HTMLTextAreaElement;

    beforeEach(() => {
        jest.clearAllMocks();
    });

    it('renders input with percent', () => {
        render(<MediaFilterValueShapeAreaPercentage value={1} onSelectionChange={onSelectionChange} />);

        expect(getInput().getAttribute('value')).toBe('100%');
    });

    it('calls onSelectionChange', () => {
        render(<MediaFilterValueShapeAreaPercentage value={0} onSelectionChange={onSelectionChange} />);

        fireEvent.input(getInput(), { target: { value: '20%' } });
        fireEvent.focusOut(getInput());

        expect(onSelectionChange).toHaveBeenCalledWith(0.2);
    });
});
