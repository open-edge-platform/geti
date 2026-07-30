// Copyright (C) 2026 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

import type { DatasetItemAnnotationStatus, Label } from '@/api/types';
import { ActionButton, Divider, Flex } from '@geti-ui/ui';
import { useDatasetFiltersSearchParams } from 'hooks/use-dataset-filters-search-params.hook';
import { useProjectLabels } from 'hooks/use-project-labels.hook';
import { capitalize, isEmpty } from 'lodash-es';

import { formatDateRangeFilter } from '../../../../shared/date-utils';
import { isNonEmptyArray } from '../../../../shared/util';
import { FilterChips } from '../toolbar/media-filtering/filter-chips/filter-chips.component';

const ANNOTATION_STATUS_LABELS: Record<DatasetItemAnnotationStatus, string> = {
    with_annotations: 'Media with annotations',
    missing_annotations: 'Media with missing annotations',
};

export const ActiveFiltersList = () => {
    const labels = useProjectLabels();
    const {
        selectedLabelIds,
        setSelectedLabelIds,
        annotationStatus,
        setAnnotationStatus,
        startDate,
        endDate,
        setDateRange,
        selectedSubsets,
        setSelectedSubsets,
    } = useDatasetFiltersSearchParams();

    const handleRemoveLabel = (id: string) => {
        setSelectedLabelIds(selectedLabelIds.filter((selectedId) => selectedId !== id));
    };

    const dateRangeLabel = formatDateRangeFilter(startDate, endDate);

    const selectedLabels = selectedLabelIds
        .map((id) => labels.find((label) => label.id === id))
        .filter(Boolean) as Label[];

    return (
        <>
            {selectedLabels.map((label) => (
                <FilterChips key={label.id} name={label.name} onClose={() => handleRemoveLabel(label.id)} />
            ))}

            {annotationStatus !== null && (
                <FilterChips
                    name={ANNOTATION_STATUS_LABELS[annotationStatus]}
                    onClose={() => setAnnotationStatus(null)}
                />
            )}

            {dateRangeLabel !== null && <FilterChips name={dateRangeLabel} onClose={() => setDateRange(null, null)} />}

            {isNonEmptyArray(selectedSubsets) &&
                selectedSubsets.map((subset) => (
                    <FilterChips
                        key={subset}
                        name={capitalize(subset)}
                        onClose={() => setSelectedSubsets(selectedSubsets.filter((sub) => sub !== subset))}
                    />
                ))}
        </>
    );
};

export const useHasActiveFilters = () => {
    const { selectedLabelIds, annotationStatus, startDate, endDate, selectedSubsets } = useDatasetFiltersSearchParams();

    return (
        !isEmpty(selectedLabelIds) ||
        annotationStatus !== null ||
        startDate !== null ||
        endDate !== null ||
        !isEmpty(selectedSubsets)
    );
};

export const useClearAllFilters = () => {
    const { setSelectedLabelIds, setAnnotationStatus, setDateRange, setSelectedSubsets } =
        useDatasetFiltersSearchParams();

    const handleClearAll = () => {
        setSelectedLabelIds([]);
        setAnnotationStatus(null);
        setDateRange(null, null);
        setSelectedSubsets([]);
    };

    return handleClearAll;
};

export const ActiveFilters = () => {
    const hasActiveFilters = useHasActiveFilters();
    const handleClearAll = useClearAllFilters();

    if (!hasActiveFilters) {
        return null;
    }

    return (
        <Flex gap={'size-150'} wrap={'wrap'} alignItems={'center'} aria-label='Active filters'>
            <ActionButton isQuiet onPress={handleClearAll}>
                Clear all
            </ActionButton>

            <Divider orientation={'vertical'} size={'S'} />

            <ActiveFiltersList />
        </Flex>
    );
};
