// INTEL CONFIDENTIAL
//
// Copyright (C) 2022 Intel Corporation
//
// This software and the related documents are Intel copyrighted materials, and your use of them is governed by
// the express license under which they were provided to you ("License"). Unless the License provides otherwise,
// you may not use, modify, copy, publish, distribute, disclose or transmit this software or the related documents
// without Intel's prior written permission.
//
// This software and the related documents are provided as is, with no express or implied warranties,
// other than those that are expressly stated in the License.

import { fireEvent, screen } from '@testing-library/react';

import { providersRender as render } from '../../../../test-utils/required-providers-render';
import { MediaFilterValueShapeAreaPercentage } from './media-filter-value-shape-area-percentage.component';

jest.mock('lodash/debounce', () => (callback: (t: string) => void) => (value: string) => callback(value));

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
