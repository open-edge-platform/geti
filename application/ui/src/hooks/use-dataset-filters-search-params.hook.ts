// Copyright (C) 2026 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

import type { DatasetItemAnnotationStatus, DatasetSubset, FilterByStatusKey } from '@/api/types';
import { parseAbsoluteToLocal } from '@internationalized/date';
import { isEmpty } from 'lodash-es';
import { useSearchParams, type SetURLSearchParams } from 'react-router-dom';
import { parse, stringify } from 'zipson/lib';

import { isNonEmptyString } from '../shared/util';
import type { SortDirection } from './sort-direction.interface';

export const LABELS_PARAM = 'labelsFilter';
export const ANNOTATION_STATUS_PARAM = 'annotationStatusFilter';
export const START_DATE_PARAM = 'startDateFilter';
export const END_DATE_PARAM = 'endDateFilter';
export const SORT_DIRECTION_PARAM = 'sortDirection';
export const SUBSET_PARAM = 'subsetFilter';

const VALID_ANNOTATION_STATUSES = new Set<DatasetItemAnnotationStatus>(['with_annotations', 'missing_annotations']);
const VALID_SUBSETS = new Set<DatasetSubset>(['unassigned', 'training', 'validation', 'testing']);

const parseAnnotationStatus = (value: string | null): DatasetItemAnnotationStatus | null => {
    if (value !== null && VALID_ANNOTATION_STATUSES.has(value as DatasetItemAnnotationStatus)) {
        return value as DatasetItemAnnotationStatus;
    }

    return null;
};

const parseSubsets = (value: string | null): DatasetSubset[] => {
    if (!isNonEmptyString(value)) {
        return [];
    }

    const subsets = value
        .split(',')
        .map((item) => item.trim())
        .filter((item): item is DatasetSubset => VALID_SUBSETS.has(item as DatasetSubset));

    return subsets;
};

// The `decodeFromBinary` and `encodeToBinary` functions are taken from,
// https://tanstack.com/router/v1/docs/guide/custom-search-param-serialization#using-zipson
// These functions make sure that the strings generated from `stringify` are properly encoded,
// even when `atob` or `btoa` do not guarantee to work with UTF8 characters
const decodeFromBinary = (str: string): string => {
    return decodeURIComponent(
        [...atob(str)].map((c) => '%' + ('00' + c.charCodeAt(0).toString(16)).slice(-2)).join('')
    );
};

export const encodeToBinary = (str: string): string => {
    return btoa(
        encodeURIComponent(str).replace(/%([0-9A-F]{2})/g, (_match, p1) => String.fromCharCode(parseInt(p1, 16)))
    );
};

const decodeLabelsParam = (raw: string): string => {
    try {
        // This may fail if the user manually changes the filter parameter in the url,
        // in that case we ignore the filter
        return (parse(decodeURIComponent(decodeFromBinary(raw ?? ''))) ?? '') as string;
    } catch {
        return '';
    }
};

const setOrDeleteParam = (params: URLSearchParams, key: string, value: string | null) => {
    if (value === null || value === undefined) {
        params.delete(key);
    } else {
        params.set(key, value);
    }
};

const updateSearchParam = (setSearchParams: SetURLSearchParams, key: string, value: string | null) => {
    setSearchParams((prev) => {
        setOrDeleteParam(prev, key, value);

        return prev;
    });
};

const parseDateFromURL = (date: string | null) => {
    if (date === null) {
        return null;
    }

    try {
        parseAbsoluteToLocal(date);

        return date;
    } catch {
        return null;
    }
};

export const useDatasetFiltersSearchParams = () => {
    const [searchParams, setSearchParams] = useSearchParams();

    const labelsFilterValue = decodeLabelsParam(searchParams.get(LABELS_PARAM) ?? '');
    const selectedLabelIds = isNonEmptyString(labelsFilterValue) ? labelsFilterValue.split(',') : [];
    const annotationStatus = parseAnnotationStatus(searchParams.get(ANNOTATION_STATUS_PARAM));
    const startDate = parseDateFromURL(searchParams.get(START_DATE_PARAM));
    const endDate = parseDateFromURL(searchParams.get(END_DATE_PARAM));
    const sortDirection: SortDirection = searchParams.get(SORT_DIRECTION_PARAM) === 'asc' ? 'asc' : 'desc';
    const selectedSubsets = parseSubsets(searchParams.get(SUBSET_PARAM));

    const setSelectedLabelIds = (ids: string[]) => {
        const newValue = isEmpty(ids) ? null : encodeToBinary(encodeURIComponent(stringify(ids.join(','))));
        updateSearchParam(setSearchParams, LABELS_PARAM, newValue);
    };

    const setAnnotationStatus = (status: FilterByStatusKey | null) => {
        updateSearchParam(setSearchParams, ANNOTATION_STATUS_PARAM, status);
    };

    const setStartDate = (date: string | null) => {
        updateSearchParam(setSearchParams, START_DATE_PARAM, date);
    };

    const setEndDate = (date: string | null) => {
        updateSearchParam(setSearchParams, END_DATE_PARAM, date);
    };

    // Updates both bounds at once, so that changing a range does not go through an intermediate state
    const setDateRange = (start: string | null, end: string | null) => {
        setSearchParams((prev) => {
            setOrDeleteParam(prev, START_DATE_PARAM, start);
            setOrDeleteParam(prev, END_DATE_PARAM, end);

            return prev;
        });
    };

    const setSortDirection = (direction: SortDirection) => {
        updateSearchParam(setSearchParams, SORT_DIRECTION_PARAM, direction);
    };

    const setSelectedSubsets = (subsets: DatasetSubset[]) => {
        const newValue = isEmpty(subsets) ? null : subsets.join(',');
        updateSearchParam(setSearchParams, SUBSET_PARAM, newValue);
    };

    return {
        selectedLabelIds,
        setSelectedLabelIds,
        annotationStatus,
        setAnnotationStatus,
        startDate,
        setStartDate,
        endDate,
        setEndDate,
        setDateRange,
        sortDirection,
        setSortDirection,
        selectedSubsets,
        setSelectedSubsets,
    } as const;
};
