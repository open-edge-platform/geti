// Copyright (C) 2026 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

import { fireEvent, screen } from '@testing-library/react';
import dayjs from 'dayjs';
import { useDatasetFiltersSearchParams } from 'hooks/use-dataset-filters-search-params.hook';
import { useProjectLabels } from 'hooks/use-project-labels.hook';
import { getMockedLabel } from 'mocks/mock-labels';
import { render } from 'test-utils/render';

import { ActiveFilters } from './active-filters.component';

vi.mock('hooks/use-project-labels.hook', () => ({
    useProjectLabels: vi.fn(),
}));

vi.mock('hooks/use-dataset-filters-search-params.hook', () => ({
    useDatasetFiltersSearchParams: vi.fn(),
}));

const mockLabels = [getMockedLabel({ id: 'label-1', name: 'Cat' }), getMockedLabel({ id: 'label-2', name: 'Dog' })];

const mockSetSelectedLabelIds = vi.fn();
const mockSetAnnotationStatus = vi.fn();
const mockSetDateRange = vi.fn();
const mockSetSelectedSubsets = vi.fn();

const mockUseDatasetFiltersSearchParams = (overrides?: Partial<ReturnType<typeof useDatasetFiltersSearchParams>>) => {
    vi.mocked(useDatasetFiltersSearchParams).mockReturnValue({
        selectedLabelIds: [],
        setSelectedLabelIds: mockSetSelectedLabelIds,
        annotationStatus: null,
        setAnnotationStatus: mockSetAnnotationStatus,
        startDate: null,
        endDate: null,
        setDateRange: mockSetDateRange,
        setSortDirection: vi.fn(),
        sortDirection: 'desc',
        selectedSubsets: [],
        setSelectedSubsets: mockSetSelectedSubsets,
        ...overrides,
    });
};

describe('ActiveFilters', () => {
    beforeEach(() => {
        vi.mocked(useProjectLabels).mockReturnValue(mockLabels);
    });

    afterEach(() => {
        vi.clearAllMocks();
    });

    it('renders nothing when there are no active filters', () => {
        mockUseDatasetFiltersSearchParams();

        render(<ActiveFilters />);

        expect(screen.queryByLabelText('Active filters')).not.toBeInTheDocument();
    });

    it('renders a chip for each selected label', () => {
        mockUseDatasetFiltersSearchParams({ selectedLabelIds: ['label-1', 'label-2'] });

        render(<ActiveFilters />);

        expect(screen.getByText('Cat')).toBeVisible();
        expect(screen.getByText('Dog')).toBeVisible();
    });

    it('renders a chip for the annotation status filter', () => {
        mockUseDatasetFiltersSearchParams({ annotationStatus: 'with_annotations' });

        render(<ActiveFilters />);

        expect(screen.getByText('Media with annotations')).toBeVisible();
    });

    it('renders a chip for the missing annotations status filter', () => {
        mockUseDatasetFiltersSearchParams({ annotationStatus: 'missing_annotations' });

        render(<ActiveFilters />);

        expect(screen.getByText('Media with missing annotations')).toBeVisible();
    });

    it('renders a single chip for the date range filter', () => {
        mockUseDatasetFiltersSearchParams({
            startDate: '2026-01-01T09:00:00.000Z',
            endDate: '2026-01-31T17:30:00.000Z',
        });

        render(<ActiveFilters />);

        const start = dayjs('2026-01-01T09:00:00.000Z').format('DD/MM/YYYY HH:mm');
        const end = dayjs('2026-01-31T17:30:00.000Z').format('DD/MM/YYYY HH:mm');

        expect(screen.getByText(`${start} - ${end}`)).toBeVisible();
    });

    it('clears both bounds when the date range chip is closed', () => {
        mockUseDatasetFiltersSearchParams({
            startDate: '2026-01-01T09:00:00.000Z',
            endDate: '2026-01-31T17:30:00.000Z',
        });

        render(<ActiveFilters />);

        fireEvent.click(screen.getByRole('button', { name: /^Remove .* filter$/ }));

        expect(mockSetDateRange).toHaveBeenCalledWith(null, null);
    });

    it('renders chips for the selected subsets', () => {
        mockUseDatasetFiltersSearchParams({ selectedSubsets: ['training', 'validation'] });

        render(<ActiveFilters />);

        expect(screen.getByText('Training')).toBeVisible();
        expect(screen.getByText('Validation')).toBeVisible();
    });

    it('removes only the clicked label when its chip is closed', () => {
        mockUseDatasetFiltersSearchParams({ selectedLabelIds: ['label-1', 'label-2'] });

        render(<ActiveFilters />);

        fireEvent.click(screen.getByRole('button', { name: 'Remove Cat filter' }));

        expect(mockSetSelectedLabelIds).toHaveBeenCalledWith(['label-2']);
    });

    it('removes only the clicked subset when its chip is closed', () => {
        mockUseDatasetFiltersSearchParams({ selectedSubsets: ['training', 'validation'] });

        render(<ActiveFilters />);

        fireEvent.click(screen.getByRole('button', { name: 'Remove Training filter' }));

        expect(mockSetSelectedSubsets).toHaveBeenCalledWith(['validation']);
    });

    it('clears all filters when "Clear all" is pressed', () => {
        mockUseDatasetFiltersSearchParams({
            selectedLabelIds: ['label-1'],
            annotationStatus: 'with_annotations',
            startDate: '2026-01-01',
            endDate: '2026-01-31',
            selectedSubsets: ['training', 'validation'],
        });

        render(<ActiveFilters />);

        fireEvent.click(screen.getByRole('button', { name: 'Clear all' }));

        expect(mockSetSelectedLabelIds).toHaveBeenCalledWith([]);
        expect(mockSetAnnotationStatus).toHaveBeenCalledWith(null);
        expect(mockSetDateRange).toHaveBeenCalledWith(null, null);
        expect(mockSetSelectedSubsets).toHaveBeenCalledWith([]);
    });
});
