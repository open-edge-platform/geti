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

import { screen } from '@testing-library/react';
import { userEvent } from '@testing-library/user-event';

import { LabelTreeLabelProps } from '../../../../../core/labels/label-tree-view.interface';
import { getMockedTreeLabel } from '../../../../../test-utils/mocked-items-factory/mocked-labels';
import { providersRender as render } from '../../../../../test-utils/required-providers-render';
import { RevisitAlertDialog } from './revisit-alert-dialog.component';

describe('revisitedAlertDialog', () => {
    it('Check if in dialog there is proper message and if save is called on buttons', async () => {
        const header = 'New Labels Alert: "Dog", "Cat", "Bird"';
        const mockSave = jest.fn();
        const labels = [
            getMockedTreeLabel({ name: 'Dog' }),
            getMockedTreeLabel({ name: 'Cat' }),
            getMockedTreeLabel({ name: 'Bird' }),
        ];

        await render(<RevisitAlertDialog flattenNewLabels={labels as LabelTreeLabelProps[]} save={mockSave} />);

        expect(screen.getByText(header)).toBeInTheDocument();
        expect(
            screen.getByText(
                /Some of your already-annotated media might be relevant to the new labels: "Dog", "Cat", "Bird"./
            )
        ).toBeInTheDocument();
        expect(screen.getByText(/Would you like to assign a "revisit" status to these media?/)).toBeInTheDocument();
        expect(
            screen.getByText(/This will help you easily identify and update annotations as required./)
        ).toBeInTheDocument();

        const assignButton = screen.getByRole('button', { name: 'Assign' });

        await userEvent.click(assignButton);
        expect(mockSave).toBeCalledWith(true);
        const dontAssignButton = screen.getByRole('button', { name: "Don't assign" });
        await userEvent.click(dontAssignButton);
        expect(mockSave).toBeCalledWith(false);
    });
});
