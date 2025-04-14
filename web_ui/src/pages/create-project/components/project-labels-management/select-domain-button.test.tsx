// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

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
