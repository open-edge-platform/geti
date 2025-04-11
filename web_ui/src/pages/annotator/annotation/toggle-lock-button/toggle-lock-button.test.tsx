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

import { fireEvent, render } from '@testing-library/react';

import { getById } from '../../../../test-utils/utils';
import { ToggleLockButton } from './toggle-lock-button.component';

describe('toggle lock button', () => {
    it("show 'lock open' icon when isHidden is false and 'lock closed' icon when parameter is true", () => {
        const onPressHandler = jest.fn();
        const { container, rerender } = render(
            <ToggleLockButton id={'test'} isDisabled={false} onPress={onPressHandler} isLocked={false} />
        );
        const iconLockClosed = getById(container, 'annotation-test-lock-open-icon');
        expect(iconLockClosed).toBeInTheDocument();

        rerender(<ToggleLockButton id={'test'} isDisabled={false} onPress={onPressHandler} isLocked={true} />);
        const iconLockOpen = getById(container, 'annotation-test-lock-closed-icon');
        expect(iconLockOpen).toBeInTheDocument();
    });

    it('onPress function handler is called after button click', () => {
        const onPressHandler = jest.fn();
        const { container } = render(
            <ToggleLockButton id={'test'} isDisabled={false} onPress={onPressHandler} isLocked={true} />
        );

        const button = getById(container, 'annotation-test-toggle-lock');
        expect(button).toBeInTheDocument();
        button && fireEvent.click(button);
        expect(onPressHandler).toHaveBeenCalled();
    });

    it('cannot click button when it is disabled', () => {
        const onPressHandler = jest.fn();
        const { container } = render(
            <ToggleLockButton id={'test'} isDisabled={true} onPress={onPressHandler} isLocked={true} />
        );

        const button = getById(container, 'annotation-test-toggle-lock');
        expect(button).toBeInTheDocument();
        button && fireEvent.click(button);
        expect(onPressHandler).not.toHaveBeenCalled();
    });
});
