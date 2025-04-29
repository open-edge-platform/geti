// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

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
