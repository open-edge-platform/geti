// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { screen } from '@testing-library/react';
import { userEvent } from '@testing-library/user-event';

import { providersRender as render } from '../../../../../test-utils/required-providers-render';
import { checkTooltip } from '../../../../../test-utils/utils';
import { AdjustmentHeader } from './adjustment-header.component';

const user = userEvent.setup({ advanceTimers: jest.advanceTimersByTime });

describe('AdjustmentHeader', () => {
    const headerText = 'Test text';
    const value = 1;
    const defaultValue = 5;
    const handleValueChange = jest.fn();

    beforeEach(() => {
        handleValueChange.mockReset();
    });

    afterAll(() => {
        jest.useRealTimers();
        jest.clearAllTimers();
    });

    it('Reset button should be visible on hover event', async () => {
        await render(
            <AdjustmentHeader
                headerText={headerText}
                value={value}
                defaultValue={defaultValue}
                handleValueChange={handleValueChange}
                formatOptions={{ style: 'percent' }}
            />
        );

        expect(screen.queryByRole('button', { name: /Reset test text/i })).not.toBeInTheDocument();
        await user.hover(screen.getByText(headerText));
        expect(screen.getByRole('button', { name: /Reset test text/i })).toBeInTheDocument();
    });

    it('Reset button should reset to default value', async () => {
        await render(
            <AdjustmentHeader
                headerText={headerText}
                value={value}
                defaultValue={defaultValue}
                handleValueChange={handleValueChange}
                formatOptions={{ style: 'percent' }}
            />
        );

        await user.hover(screen.getByText(headerText));
        await user.click(screen.getByRole('button', { name: /Reset test text/i }));
        expect(handleValueChange).toHaveBeenCalledWith(defaultValue);
    });

    it('Value should be displayed in percentages', async () => {
        await render(
            <AdjustmentHeader
                headerText={headerText}
                value={value}
                defaultValue={defaultValue}
                handleValueChange={handleValueChange}
                formatOptions={{ style: 'percent' }}
            />
        );

        expect(screen.getByText(`${value * 100}%`)).toBeInTheDocument();
    });

    it('tooltip for reset button should be displayed', async () => {
        jest.useFakeTimers();

        await render(
            <AdjustmentHeader
                headerText={headerText}
                value={value}
                defaultValue={defaultValue}
                handleValueChange={handleValueChange}
                formatOptions={{ style: 'percent' }}
            />
        );

        await user.hover(screen.getByText(headerText));

        await checkTooltip(
            screen.getByRole('button', { name: /Reset test text/i }),
            `Reset to default value ${headerText.toLocaleLowerCase()}`
        );

        jest.useRealTimers();
    });
});
