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

import { providersRender as render } from '../../../../../test-utils/required-providers-render';
import { ToggleableChevron } from './search-label-tree-view-item.component';

describe('ToggleableChevron', () => {
    it('Cannot expand label hierarchy in label selection tool (top-left)', async () => {
        const toggleHandler = jest.fn();
        render(<ToggleableChevron isOpen={false} toggle={toggleHandler} id={'test'} />);

        await userEvent.click(screen.getByRole('button', { name: 'Click to show child labels' }));

        expect(toggleHandler).toHaveBeenCalled();
    });
});
