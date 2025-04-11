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

import { fireEvent, screen } from '@testing-library/react';

import { LabelsRelationType } from '../../../core/labels/label.interface';
import { getLabelId } from '../../../core/labels/utils';
import { getMockedTreeGroup, getMockedTreeLabel } from '../../../test-utils/mocked-items-factory/mocked-labels';
import { providersRender as render } from '../../../test-utils/required-providers-render';
import { checkTooltip, getById } from '../../../test-utils/utils';
import { TaskLabelTreeItem } from './task-label-tree-item.component';

describe('TaskLabelTreeItem', () => {
    afterAll(() => {
        jest.useRealTimers();
        jest.clearAllTimers();
    });

    it('render suffix and color thumb', async () => {
        const mockOnClick = jest.fn();
        const subffixText = 'label-suffix';
        const label = getMockedTreeLabel({
            name: 'Animal',
            relation: LabelsRelationType.SINGLE_SELECTION,
        });

        const { container } = await render(
            <TaskLabelTreeItem suffix={() => <div>{subffixText}</div>} onClick={mockOnClick} level={2} label={label}>
                <></>
            </TaskLabelTreeItem>
        );

        fireEvent.click(screen.getByText(label.name));

        expect(screen.getByText(subffixText)).toBeVisible();
        expect(getById(container, `${getLabelId('tree', label)}-color`)).toBeVisible();
        expect(mockOnClick).toHaveBeenCalledWith(label);
    });

    describe('groups', () => {
        it('shows label relation tooltip', async () => {
            jest.useFakeTimers();
            const mockOnClick = jest.fn();

            await render(
                <TaskLabelTreeItem
                    suffix={() => <></>}
                    onClick={mockOnClick}
                    level={0}
                    label={getMockedTreeGroup({
                        name: 'Animal',
                        relation: LabelsRelationType.SINGLE_SELECTION,
                    })}
                >
                    <></>
                </TaskLabelTreeItem>
            );

            await checkTooltip(screen.getByLabelText('label-relation'), LabelsRelationType.SINGLE_SELECTION);
        });

        it('toggle open/close labels', async () => {
            const label = getMockedTreeGroup({
                name: 'Animal',
                open: true,
                relation: LabelsRelationType.SINGLE_SELECTION,
                children: [getMockedTreeLabel({ name: 'Cat' }), getMockedTreeLabel({ name: 'Dog' })],
            });
            await render(
                <TaskLabelTreeItem suffix={() => <></>} onClick={jest.fn()} level={0} label={label}>
                    <div></div>
                </TaskLabelTreeItem>
            );

            expect(screen.getByLabelText('label open')).toBeVisible();

            const toggleableChevron = screen.getByLabelText(`toggleable chevron ${label.id}`);
            expect(toggleableChevron).toBeVisible();
            fireEvent.click(toggleableChevron);

            expect(screen.getByLabelText('label close')).toBeVisible();
        });
    });
});
