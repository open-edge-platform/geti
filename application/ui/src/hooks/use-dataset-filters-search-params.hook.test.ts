// Copyright (C) 2026 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

import { act } from '@testing-library/react';
import { useSearchParams } from 'react-router';
import { stringify } from 'zipson/lib';

import { renderHook } from '../test-utils/render';
import {
    ANNOTATION_STATUS_PARAM,
    encodeToBinary,
    END_DATE_PARAM,
    LABELS_PARAM,
    SORT_DIRECTION_PARAM,
    START_DATE_PARAM,
    SUBSET_PARAM,
    useDatasetFiltersSearchParams,
} from './use-dataset-filters-search-params.hook';

describe('useDatasetFiltersSearchParams', () => {
    describe('labels filter', () => {
        it('returns empty selectedLabelIds when no filter param is present', () => {
            const { result } = renderHook(() => useDatasetFiltersSearchParams(), {
                route: '/projects/123',
                path: '/projects/:projectId',
            });

            expect(result.current.selectedLabelIds).toEqual([]);
        });

        it('returns selectedLabelIds from encoded filter param', () => {
            const encoded = encodeToBinary(stringify('id-1,id-2,id-3'));

            const { result } = renderHook(() => useDatasetFiltersSearchParams(), {
                route: `/projects/123?${LABELS_PARAM}=${encoded}`,
                path: '/projects/:projectId',
            });

            expect(result.current.selectedLabelIds).toEqual(['id-1', 'id-2', 'id-3']);
        });

        it('returns a single label id', () => {
            const labelName = 'id-1';
            const encoded = encodeToBinary(stringify(labelName));

            const { result } = renderHook(() => useDatasetFiltersSearchParams(), {
                route: `/projects/123?${LABELS_PARAM}=${encoded}`,
                path: '/projects/:projectId',
            });

            expect(result.current.selectedLabelIds).toEqual([labelName]);
        });

        it('sets selected label ids in the search params', () => {
            const newLabels = ['id-a', 'id-b'];
            const { result } = renderHook(() => useDatasetFiltersSearchParams(), {
                route: '/projects/123',
                path: '/projects/:projectId',
            });

            act(() => {
                result.current.setSelectedLabelIds(newLabels);
            });

            expect(result.current.selectedLabelIds).toEqual(newLabels);
        });

        it('clears filter param when setting empty ids', () => {
            const labelName = 'id-1';
            const encoded = encodeToBinary(stringify(labelName));

            const { result } = renderHook(() => useDatasetFiltersSearchParams(), {
                route: `/projects/123?${LABELS_PARAM}=${encoded}`,
                path: '/projects/:projectId',
            });

            expect(result.current.selectedLabelIds).toEqual([labelName]);

            act(() => {
                result.current.setSelectedLabelIds([]);
            });

            expect(result.current.selectedLabelIds).toEqual([]);
        });

        it('returns empty array when filter param is malformed', () => {
            const { result } = renderHook(() => useDatasetFiltersSearchParams(), {
                route: `/projects/123?${LABELS_PARAM}=invalid-data`,
                path: '/projects/:projectId',
            });

            expect(result.current.selectedLabelIds).toEqual([]);
        });

        it('returns null annotationStatus when no param is present', () => {
            const { result } = renderHook(() => useDatasetFiltersSearchParams(), {
                route: '/projects/123',
                path: '/projects/:projectId',
            });

            expect(result.current.annotationStatus).toBeNull();
        });
    });

    describe('annotationStatus filter', () => {
        it.each(['missing_annotations', 'with_annotations'] as const)(
            'returns annotationStatus "%s" from search param',
            (status) => {
                const { result } = renderHook(() => useDatasetFiltersSearchParams(), {
                    route: `/projects/123?${ANNOTATION_STATUS_PARAM}=${status}`,
                    path: '/projects/:projectId',
                });

                expect(result.current.annotationStatus).toBe(status);
            }
        );

        it('returns null annotationStatus for invalid value', () => {
            const { result } = renderHook(() => useDatasetFiltersSearchParams(), {
                route: `/projects/123?${ANNOTATION_STATUS_PARAM}=invalid`,
                path: '/projects/:projectId',
            });

            expect(result.current.annotationStatus).toBeNull();
        });

        it('sets annotation status in the search params', () => {
            const { result } = renderHook(() => useDatasetFiltersSearchParams(), {
                route: '/projects/123',
                path: '/projects/:projectId',
            });

            act(() => {
                result.current.setAnnotationStatus('with_annotations');
            });

            expect(result.current.annotationStatus).toBe('with_annotations');
        });

        it('clears annotation status when set to null', () => {
            const { result } = renderHook(() => useDatasetFiltersSearchParams(), {
                route: `/projects/123?${ANNOTATION_STATUS_PARAM}=with_annotations`,
                path: '/projects/:projectId',
            });

            expect(result.current.annotationStatus).toBe('with_annotations');

            act(() => {
                result.current.setAnnotationStatus(null);
            });

            expect(result.current.annotationStatus).toBeNull();
        });
    });

    describe('subset filter', () => {
        it.each(['training', 'validation', 'testing', 'unassigned'] as const)(
            'returns subset "%s" from search param',
            (subset) => {
                const { result } = renderHook(() => useDatasetFiltersSearchParams(), {
                    route: `/projects/123?${SUBSET_PARAM}=${subset}`,
                    path: '/projects/:projectId',
                });

                expect(result.current.selectedSubsets).toEqual([subset]);
            }
        );

        it('returns multiple subsets from a comma-separated search param', () => {
            const { result } = renderHook(() => useDatasetFiltersSearchParams(), {
                route: `/projects/123?${SUBSET_PARAM}=training,validation`,
                path: '/projects/:projectId',
            });

            expect(result.current.selectedSubsets).toEqual(['training', 'validation']);
        });

        it('returns empty array when no param is present', () => {
            const { result } = renderHook(() => useDatasetFiltersSearchParams(), {
                route: '/projects/123',
                path: '/projects/:projectId',
            });

            expect(result.current.selectedSubsets).toEqual([]);
        });

        it('ignores invalid values while keeping valid ones', () => {
            const { result } = renderHook(() => useDatasetFiltersSearchParams(), {
                route: `/projects/123?${SUBSET_PARAM}=training,invalid`,
                path: '/projects/:projectId',
            });

            expect(result.current.selectedSubsets).toEqual(['training']);
        });

        it('trims whitespace around each value before validating', () => {
            const { result } = renderHook(() => useDatasetFiltersSearchParams(), {
                route: `/projects/123?${SUBSET_PARAM}=${encodeURIComponent('training, validation , testing')}`,
                path: '/projects/:projectId',
            });

            expect(result.current.selectedSubsets).toEqual(['training', 'validation', 'testing']);
        });

        it('returns empty array when the param is entirely invalid', () => {
            const { result } = renderHook(() => useDatasetFiltersSearchParams(), {
                route: `/projects/123?${SUBSET_PARAM}=invalid`,
                path: '/projects/:projectId',
            });

            expect(result.current.selectedSubsets).toEqual([]);
        });

        it('sets multiple subsets in the search params', () => {
            const { result } = renderHook(() => useDatasetFiltersSearchParams(), {
                route: '/projects/123',
                path: '/projects/:projectId',
            });

            act(() => {
                result.current.setSelectedSubsets(['training', 'validation', 'testing']);
            });

            expect(result.current.selectedSubsets).toEqual(['training', 'validation', 'testing']);
        });

        it('clears subsets when set to an empty array', () => {
            const { result } = renderHook(() => useDatasetFiltersSearchParams(), {
                route: `/projects/123?${SUBSET_PARAM}=training,validation`,
                path: '/projects/:projectId',
            });

            expect(result.current.selectedSubsets).toEqual(['training', 'validation']);

            act(() => {
                result.current.setSelectedSubsets([]);
            });

            expect(result.current.selectedSubsets).toEqual([]);
        });
    });

    describe('date filters', () => {
        it('returns null startDate and endDate when no params are present', () => {
            const { result } = renderHook(() => useDatasetFiltersSearchParams(), {
                route: '/projects/123',
                path: '/projects/:projectId',
            });

            expect(result.current.startDate).toBeNull();
            expect(result.current.endDate).toBeNull();
        });

        it('returns startDate from search param', () => {
            const { result } = renderHook(() => useDatasetFiltersSearchParams(), {
                route: `/projects/123?${START_DATE_PARAM}=2026-01-01T22:00:00.000Z`,
                path: '/projects/:projectId',
            });

            expect(result.current.startDate).toBe('2026-01-01T22:00:00.000Z');
        });

        it('returns endDate from search param', () => {
            const { result } = renderHook(() => useDatasetFiltersSearchParams(), {
                route: `/projects/123?${END_DATE_PARAM}=2026-12-31T10:00:00.000Z`,
                path: '/projects/:projectId',
            });

            expect(result.current.endDate).toBe('2026-12-31T10:00:00.000Z');
        });

        it('sets startDate in the search params', () => {
            const { result } = renderHook(() => useDatasetFiltersSearchParams(), {
                route: '/projects/123',
                path: '/projects/:projectId',
            });

            act(() => {
                result.current.setStartDate('2026-03-15T22:00:00.000Z');
            });

            expect(result.current.startDate).toBe('2026-03-15T22:00:00.000Z');
        });

        it('sets endDate in the search params', () => {
            const { result } = renderHook(() => useDatasetFiltersSearchParams(), {
                route: '/projects/123',
                path: '/projects/:projectId',
            });

            act(() => {
                result.current.setEndDate('2026-06-30T10:00:00.000Z');
            });

            expect(result.current.endDate).toBe('2026-06-30T10:00:00.000Z');
        });

        it('clears startDate when set to null', () => {
            const { result } = renderHook(() => useDatasetFiltersSearchParams(), {
                route: `/projects/123?${START_DATE_PARAM}=2026-01-01T22:00:00.000Z`,
                path: '/projects/:projectId',
            });

            expect(result.current.startDate).toBe('2026-01-01T22:00:00.000Z');

            act(() => {
                result.current.setStartDate(null);
            });

            expect(result.current.startDate).toBeNull();
        });

        it('clears endDate when set to null', () => {
            const { result } = renderHook(() => useDatasetFiltersSearchParams(), {
                route: `/projects/123?${END_DATE_PARAM}=2026-12-31T10:00:00.000Z`,
                path: '/projects/:projectId',
            });

            expect(result.current.endDate).toBe('2026-12-31T10:00:00.000Z');

            act(() => {
                result.current.setEndDate(null);
            });

            expect(result.current.endDate).toBeNull();
        });

        it('returns both startDate and endDate when both params are present', () => {
            const { result } = renderHook(() => useDatasetFiltersSearchParams(), {
                route: `/projects/123?${START_DATE_PARAM}=2026-01-01T22:00:00.000Z&${END_DATE_PARAM}=2026-12-31T10:00:00.000Z`,
                path: '/projects/:projectId',
            });

            expect(result.current.startDate).toBe('2026-01-01T22:00:00.000Z');
            expect(result.current.endDate).toBe('2026-12-31T10:00:00.000Z');
        });

        it('returns null startDate when the param is not a valid absolute timestamp', () => {
            const { result } = renderHook(() => useDatasetFiltersSearchParams(), {
                route: `/projects/123?${START_DATE_PARAM}=2026-01-01`,
                path: '/projects/:projectId',
            });

            expect(result.current.startDate).toBeNull();
        });
    });

    describe('sort direction filter', () => {
        it('defaults to "desc" when no param is present', () => {
            const { result } = renderHook(() => useDatasetFiltersSearchParams(), {
                route: '/projects/123',
                path: '/projects/:projectId',
            });

            expect(result.current.sortDirection).toBe('desc');
        });

        it.each(['asc', 'desc'] as const)('returns sortDirection "%s" from search param', (direction) => {
            const { result } = renderHook(() => useDatasetFiltersSearchParams(), {
                route: `/projects/123?${SORT_DIRECTION_PARAM}=${direction}`,
                path: '/projects/:projectId',
            });

            expect(result.current.sortDirection).toBe(direction);
        });

        it('defaults to "desc" for an invalid value', () => {
            const { result } = renderHook(() => useDatasetFiltersSearchParams(), {
                route: `/projects/123?${SORT_DIRECTION_PARAM}=invalid`,
                path: '/projects/:projectId',
            });

            expect(result.current.sortDirection).toBe('desc');
        });

        it('sets sortDirection in the search params and reads it back', () => {
            const { result } = renderHook(() => useDatasetFiltersSearchParams(), {
                route: '/projects/123',
                path: '/projects/:projectId',
            });

            expect(result.current.sortDirection).toBe('desc');

            act(() => {
                result.current.setSortDirection('asc');
            });

            expect(result.current.sortDirection).toBe('asc');

            act(() => {
                result.current.setSortDirection('desc');
            });

            expect(result.current.sortDirection).toBe('desc');
        });
    });

    describe('clearAllFilters', () => {
        it('clears every filter in one update', () => {
            const encoded = encodeToBinary(stringify('id-1'));
            const route =
                `/projects/123?${LABELS_PARAM}=${encoded}` +
                `&${ANNOTATION_STATUS_PARAM}=with_annotations` +
                `&${START_DATE_PARAM}=2026-03-15T22:00:00.000Z` +
                `&${END_DATE_PARAM}=2026-06-30T10:00:00.000Z` +
                `&${SUBSET_PARAM}=training`;

            const { result } = renderHook(() => useDatasetFiltersSearchParams(), {
                route,
                path: '/projects/:projectId',
            });

            act(() => {
                result.current.clearAllFilters();
            });

            expect(result.current.selectedLabelIds).toEqual([]);
            expect(result.current.annotationStatus).toBeNull();
            expect(result.current.startDate).toBeNull();
            expect(result.current.endDate).toBeNull();
            expect(result.current.selectedSubsets).toEqual([]);
        });

        it('keeps search params that are not filters', () => {
            const route = `/projects/123?${ANNOTATION_STATUS_PARAM}=with_annotations&${SORT_DIRECTION_PARAM}=asc&datasetViewId=collection-one`;

            const { result } = renderHook(
                () => ({ filters: useDatasetFiltersSearchParams(), searchParams: useSearchParams()[0] }),
                { route, path: '/projects/:projectId' }
            );

            act(() => {
                result.current.filters.clearAllFilters();
            });

            expect(result.current.filters.annotationStatus).toBeNull();
            expect(result.current.filters.sortDirection).toBe('asc');
            expect(result.current.searchParams.get('datasetViewId')).toBe('collection-one');
        });
    });
});
