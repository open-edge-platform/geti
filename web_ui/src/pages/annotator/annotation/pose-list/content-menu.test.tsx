// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

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
