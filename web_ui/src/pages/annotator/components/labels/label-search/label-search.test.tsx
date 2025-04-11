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

import '@wessberg/pointer-events';

import { fireEvent, screen } from '@testing-library/react';

import { labels } from '../../../../../test-utils/mocked-items-factory/mocked-labels';
import { providersRender as render } from '../../../../../test-utils/required-providers-render';
import { hover } from '../../../../../test-utils/utils';
import { LabelSearch } from './label-search.component';

describe('Default label combobox', () => {
    it('Searches labels and shows their parents', () => {
        const onClick = jest.fn();

        render(<LabelSearch labels={labels} onClick={onClick} />);

        expect(screen.getAllByRole('listitem')).toHaveLength(11);

        const input = screen.getByRole('textbox');

        fireEvent.input(input, { target: { value: labels[6].name } });

        expect(screen.getAllByRole('listitem')).toHaveLength(3);

        expect(screen.getByText('card')).toBeInTheDocument();
        expect(screen.getByText('black')).toBeInTheDocument();
        expect(screen.getByText('♣')).toBeInTheDocument();

        fireEvent.click(screen.getByLabelText(`label item ${labels[6].name}`));

        expect(onClick).toHaveBeenCalledWith(expect.objectContaining(labels[6]));
    });

    it('shows no results', () => {
        const onClick = jest.fn();

        render(<LabelSearch labels={labels} onClick={onClick} />);

        expect(screen.getAllByRole('listitem')).toHaveLength(11);

        const input = screen.getByRole('textbox');
        fireEvent.input(input, { target: { value: 'An unknown label' } });

        expect(screen.queryAllByRole('listitem')).toHaveLength(0);
        expect(screen.getByText('No Results')).toBeInTheDocument();
    });

    it('can open and close a group of labels', () => {
        const onClick = jest.fn();

        render(<LabelSearch labels={labels} onClick={onClick} />);

        const first = screen.getAllByLabelText('Click to show child labels')[0];
        fireEvent.click(first);

        expect(screen.getAllByLabelText('Click to show child labels')).toHaveLength(2);
        expect(screen.getAllByLabelText('Click to hide child labels')).toHaveLength(1);

        fireEvent.click(first);

        expect(screen.queryAllByLabelText('Click to hide child labels')).toHaveLength(0);
    });

    // This is specifically useful in task chain projects where a label may have a
    // parent label from a different task
    it('shows labels without parents', () => {
        const [parentLabel, ...parentLessLabels] = labels;

        const onClick = jest.fn();

        render(<LabelSearch labels={parentLessLabels} onClick={onClick} />);

        expect(screen.getAllByRole('listitem')).toHaveLength(10);

        const input = screen.getByRole('textbox');
        fireEvent.input(input, { target: { value: '♣' } });

        expect(screen.getAllByRole('listitem')).toHaveLength(2);

        expect(screen.queryByText(parentLabel.name)).not.toBeInTheDocument();
        expect(screen.getByText('black')).toBeInTheDocument();
        expect(screen.getByText('♣')).toBeInTheDocument();
    });

    it('allows to render a custom suffix for each label', async () => {
        const onClick = jest.fn();

        render(
            <LabelSearch
                labels={labels}
                onClick={onClick}
                suffix={(_label, { isHovered }) => {
                    return <span>{isHovered ? 'Hovered' : 'Not hovered'}</span>;
                }}
            />
        );

        const input = screen.getByRole('textbox', {
            name: /select label/i,
        });

        fireEvent.input(input, { target: { value: '♣' } });

        expect(
            screen.getByRole('textbox', {
                name: /select label/i,
            })
        ).toHaveValue('♣');

        expect(screen.getAllByRole('listitem')).toHaveLength(3);

        expect(screen.getByText('black')).toBeInTheDocument();
        expect(screen.getByText('♣')).toBeInTheDocument();

        expect(screen.queryAllByText('Hovered')).toHaveLength(0);
        expect(screen.getAllByText('Not hovered')).toHaveLength(3);

        // Hover over a label list item
        hover(screen.getByText('♣'));

        expect(await screen.findAllByText('Hovered')).toHaveLength(1);
    });
});
