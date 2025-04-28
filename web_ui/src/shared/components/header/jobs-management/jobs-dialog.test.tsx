// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { CalendarDate, getLocalTimeZone, today } from '@internationalized/date';
import { RangeValue } from '@react-types/shared';
import { fireEvent, screen } from '@testing-library/react';

import { providersRender as render } from '../../../../test-utils/required-providers-render';
import { JobsDialog } from './jobs-dialog.component';

jest.mock('react-router-dom', () => ({
    ...jest.requireActual('react-router-dom'),
    useParams: () => ({
        organizationId: 'organization-id',
        workspaceId: 'workspace_1',
    }),
}));

describe('jobs dialog', (): void => {
    beforeEach((): void => {
        jest.clearAllMocks();
    });

    const TODAY = today(getLocalTimeZone());
    const INITIAL_DATES: RangeValue<CalendarDate> = {
        start: TODAY.subtract({ months: 3 }),
        end: TODAY,
    };

    const renderComponent = () => {
        render(<JobsDialog onClose={jest.fn()} isFullScreen={false} setIsFullScreen={jest.fn()} />);
    };

    it('should properly render job management dialog', async (): Promise<void> => {
        renderComponent();

        expect(screen.getByRole('dialog')).toBeVisible();

        expect(screen.getByLabelText('Job scheduler filter project')).toBeInTheDocument();
        expect(screen.getByLabelText('Job scheduler filter user')).toBeInTheDocument();
        expect(screen.getByLabelText('Job scheduler filter job type')).toBeInTheDocument();

        expect(screen.getByRole('tablist', { name: 'Job management tabs' })).toBeInTheDocument();

        expect(screen.getByRole('tab', { name: 'Running jobs' })).toBeInTheDocument();
        expect(screen.getByRole('tab', { name: 'Running jobs' })).toHaveAttribute('aria-selected', 'true');

        expect(screen.getByRole('tab', { name: 'Finished jobs' })).toBeInTheDocument();
        expect(screen.getByRole('tab', { name: 'Scheduled jobs' })).toBeInTheDocument();
        expect(screen.getByRole('tab', { name: 'Cancelled jobs' })).toBeInTheDocument();
        expect(screen.getByRole('tab', { name: 'Failed jobs' })).toBeInTheDocument();
    });

    it('should properly switch between job management tabs', async (): Promise<void> => {
        renderComponent();

        expect(screen.getByRole('tab', { name: 'Running jobs' })).toBeInTheDocument();
        expect(screen.getByRole('tab', { name: 'Finished jobs' })).toBeInTheDocument();
        expect(screen.getByRole('tab', { name: 'Scheduled jobs' })).toBeInTheDocument();
        expect(screen.getByRole('tab', { name: 'Cancelled jobs' })).toBeInTheDocument();
        expect(screen.getByRole('tab', { name: 'Failed jobs' })).toBeInTheDocument();

        expect(screen.getByRole('tab', { name: 'Running jobs' })).toHaveAttribute('aria-selected', 'true');

        fireEvent.click(screen.getByRole('tab', { name: 'Finished jobs' }));
        expect(screen.getByRole('tab', { name: 'Running jobs' })).toHaveAttribute('aria-selected', 'false');
        expect(screen.getByRole('tab', { name: 'Finished jobs' })).toHaveAttribute('aria-selected', 'true');

        fireEvent.click(screen.getByRole('tab', { name: 'Scheduled jobs' }));
        expect(screen.getByRole('tab', { name: 'Running jobs' })).toHaveAttribute('aria-selected', 'false');
        expect(screen.getByRole('tab', { name: 'Finished jobs' })).toHaveAttribute('aria-selected', 'false');
        expect(screen.getByRole('tab', { name: 'Scheduled jobs' })).toHaveAttribute('aria-selected', 'true');

        fireEvent.click(screen.getByRole('tab', { name: 'Cancelled jobs' }));
        expect(screen.getByRole('tab', { name: 'Running jobs' })).toHaveAttribute('aria-selected', 'false');
        expect(screen.getByRole('tab', { name: 'Finished jobs' })).toHaveAttribute('aria-selected', 'false');
        expect(screen.getByRole('tab', { name: 'Scheduled jobs' })).toHaveAttribute('aria-selected', 'false');
        expect(screen.getByRole('tab', { name: 'Cancelled jobs' })).toHaveAttribute('aria-selected', 'true');

        fireEvent.click(screen.getByRole('tab', { name: 'Failed jobs' }));
        expect(screen.getByRole('tab', { name: 'Running jobs' })).toHaveAttribute('aria-selected', 'false');
        expect(screen.getByRole('tab', { name: 'Finished jobs' })).toHaveAttribute('aria-selected', 'false');
        expect(screen.getByRole('tab', { name: 'Scheduled jobs' })).toHaveAttribute('aria-selected', 'false');
        expect(screen.getByRole('tab', { name: 'Cancelled jobs' })).toHaveAttribute('aria-selected', 'false');
        expect(screen.getByRole('tab', { name: 'Failed jobs' })).toHaveAttribute('aria-selected', 'true');
    });

    describe('JobsDialog - Filtering by Dates', () => {
        it('should render the DateRangePickerSmall component with initial date range', () => {
            renderComponent();

            const fromDateField = screen.getByLabelText('From');
            const toDateField = screen.getByLabelText('To');

            expect(fromDateField).toHaveValue(INITIAL_DATES.start.toString());
            expect(toDateField).toHaveValue(INITIAL_DATES.end.toString());
        });

        it('should update the date range when a new range is selected', () => {
            renderComponent();

            const fromDateField = screen.getByLabelText('From');
            const toDateField = screen.getByLabelText('To');

            // Simulate user selecting a new date range
            fireEvent.change(fromDateField, { target: { value: TODAY.subtract({ days: 7 }).toString() } });
            fireEvent.change(toDateField, { target: { value: TODAY.toString() } });

            expect(fromDateField).toHaveValue(TODAY.subtract({ days: 7 }).toString());
            expect(toDateField).toHaveValue(TODAY.toString());
        });

        it('should reset the date range to the initial range when the reset button is clicked', () => {
            renderComponent();

            const fromDateField = screen.getByLabelText('From');
            const toDateField = screen.getByLabelText('To');
            const resetButton = screen.getByLabelText('Reset all filters');

            // Simulate user selecting a new date range
            fireEvent.change(fromDateField, { target: { value: TODAY.subtract({ days: 7 }).toString() } });
            fireEvent.change(toDateField, { target: { value: TODAY.toString() } });

            // Simulate clicking the reset button
            fireEvent.click(resetButton);

            expect(fromDateField).toHaveValue(INITIAL_DATES.start.toString());
            expect(toDateField).toHaveValue(INITIAL_DATES.end.toString());
        });

        it('should call the onChange handler when the date range is updated', () => {
            const mockHandleRangeChange = jest.fn();
            render(<JobsDialog isFullScreen={false} onClose={jest.fn()} setIsFullScreen={jest.fn()} />);

            const fromDateField = screen.getByLabelText('From');
            const toDateField = screen.getByLabelText('To');

            // Simulate user selecting a new date range
            fireEvent.change(fromDateField, { target: { value: TODAY.subtract({ days: 7 }).toString() } });
            fireEvent.change(toDateField, { target: { value: TODAY.toString() } });

            expect(mockHandleRangeChange).toHaveBeenCalledWith({
                start: TODAY.subtract({ days: 7 }),
                end: TODAY,
            });
        });
    });
});
