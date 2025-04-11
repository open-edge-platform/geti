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

import { fireEvent, render, screen } from '@testing-library/react';

import { getById } from '../../../../test-utils/utils';
import { SelectDomainButton } from './select-domain-button.component';

describe('select domain button', () => {
    const select = jest.fn();

    it('onPress selection is called', () => {
        const { container } = render(
            <SelectDomainButton
                taskNumber={1}
                id={'test-domain-button'}
                text={'Test domain'}
                select={select}
                isSelected={false}
            />
        );

        const button = getById(container, 'test-domain-button');
        button && fireEvent.click(button);
        expect(select).toBeCalled();
    });

    it('button has proper text', () => {
        render(
            <SelectDomainButton
                taskNumber={1}
                id={'test-domain-button'}
                text={'Test domain'}
                select={select}
                isSelected={false}
            />
        );

        const test = screen.getByText('Test domain');
        expect(test).toBeInTheDocument();
    });
});
