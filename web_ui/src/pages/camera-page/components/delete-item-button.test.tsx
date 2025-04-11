// INTEL CONFIDENTIAL
//
// Copyright (C) 2024 Intel Corporation
//
// This software and the related documents are Intel copyrighted materials, and your use of them is governed by
// the express license under which they were provided to you ("License"). Unless the License provides otherwise,
// you may not use, modify, copy, publish, distribute, disclose or transmit this software or the related documents
// without Intel's prior written permission.
//
// This software and the related documents are provided as is, with no express or implied warranties,
// other than those that are expressly stated in the License.

import { fireEvent, screen } from '@testing-library/react';
import { useOverlayTriggerState } from 'react-stately';

import { providersRender } from '../../../test-utils/required-providers-render';
import { DeleteItemButton } from './delete-item-button.component';

describe('DeleteItemButton', () => {
    const renderAp = async ({ id = 'test-id', onDeleteItem = jest.fn() }: { id?: string; onDeleteItem: jest.Mock }) => {
        const StateDeleteItemButton = () => {
            const alertDialogState = useOverlayTriggerState({});
            return <DeleteItemButton id={id} alertDialogState={alertDialogState} onDeleteItem={onDeleteItem} />;
        };

        providersRender(<StateDeleteItemButton />);
    };

    it('calls onDeleteItem', async () => {
        const mockedDelete = jest.fn();
        const mockedId = 'item-id';

        await renderAp({ id: mockedId, onDeleteItem: mockedDelete });

        fireEvent.click(screen.getByRole('button', { name: /delete/ }));

        fireEvent.click(await screen.findByRole('button', { name: /delete/i }));

        expect(mockedDelete).toHaveBeenCalledTimes(1);
    });
});
