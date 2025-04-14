// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { fireEvent, render } from '@testing-library/react';
import { userEvent } from '@testing-library/user-event';

import { getById } from '../../../../test-utils/utils';
import { ToggleVisibilityButton } from './toggle-visibility-button.component';

describe('toggle visibility button', () => {
    it("show 'visibility on' icon when isHidden is false and 'visibility off' icon when parameter is true", () => {
        const onPressHandler = jest.fn();
        const { container, rerender } = render(
            <ToggleVisibilityButton id={'test'} isDisabled={false} onPress={onPressHandler} isHidden={false} />
        );
        const iconVisibilityOn = getById(container, 'annotation-test-visibility-on-icon');

        expect(iconVisibilityOn).toBeInTheDocument();

        rerender(<ToggleVisibilityButton id={'test'} isDisabled={false} onPress={onPressHandler} isHidden />);

        const iconVisibilityOff = getById(container, 'annotation-test-visibility-off-icon');

        expect(iconVisibilityOff).toBeInTheDocument();
    });

    it('onPress function handler is called after button click', () => {
        const onPressHandler = jest.fn();
        const { container } = render(
            <ToggleVisibilityButton id={'test'} isDisabled={false} onPress={onPressHandler} isHidden />
        );

        const button = getById(container, 'annotation-test-toggle-visibility');

        expect(button).toBeInTheDocument();

        button && fireEvent.click(button);

        expect(onPressHandler).toHaveBeenCalled();
    });

    it('cannot click button when it is disabled', () => {
        const onPressHandler = jest.fn();
        const { container } = render(
            <ToggleVisibilityButton id={'test'} isDisabled onPress={onPressHandler} isHidden />
        );

        const button = getById(container, 'annotation-test-toggle-visibility');
        expect(button).toBeInTheDocument();

        button && fireEvent.click(button);

        expect(onPressHandler).not.toHaveBeenCalled();
    });

    it('handler is called when using shortcut and button is enabled', async () => {
        const onPressHandler = jest.fn();

        render(<ToggleVisibilityButton id={'test'} isDisabled={false} onPress={onPressHandler} isHidden />);

        expect(onPressHandler).not.toHaveBeenCalled();

        await userEvent.keyboard('A');

        expect(onPressHandler).toHaveBeenCalled();
    });

    it('handler is not called when using shortcut and button is disabled', async () => {
        const onPressHandler = jest.fn();

        render(<ToggleVisibilityButton id={'test'} isDisabled onPress={onPressHandler} isHidden />);

        expect(onPressHandler).not.toHaveBeenCalled();

        await userEvent.keyboard('A');

        expect(onPressHandler).not.toHaveBeenCalled();
    });
});
