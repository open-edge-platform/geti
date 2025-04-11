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

import { getMockedKeypointNode } from '../../../../test-utils/mocked-items-factory/mocked-keypoint';
import { providersRender as render } from '../../../../test-utils/required-providers-render';
import { ContentMenu, OPTION_OCCLUDED, OPTION_VISIBLE } from './content-menu.component';

describe('ContentMenu', () => {
    it('mark the point as hidden if it was visible before', () => {
        const mockedOnUpdate = jest.fn();

        render(<ContentMenu point={getMockedKeypointNode({ isVisible: true })} onUpdate={mockedOnUpdate} />);

        fireEvent.click(screen.getByLabelText('menu trigger'));
        fireEvent.click(screen.getByRole('menuitem', { name: OPTION_OCCLUDED }));

        expect(mockedOnUpdate).toHaveBeenCalledWith(expect.objectContaining({ isVisible: false }));
    });

    it('mark the point as visible if it was hidden before', () => {
        const mockedOnUpdate = jest.fn();

        render(<ContentMenu point={getMockedKeypointNode({ isVisible: false })} onUpdate={mockedOnUpdate} />);

        fireEvent.click(screen.getByLabelText('menu trigger'));
        fireEvent.click(screen.getByRole('menuitem', { name: OPTION_VISIBLE }));

        expect(mockedOnUpdate).toHaveBeenCalledWith(expect.objectContaining({ isVisible: true }));
    });
});
