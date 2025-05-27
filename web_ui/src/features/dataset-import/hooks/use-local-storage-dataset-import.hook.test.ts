// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { renderHook, act } from '@testing-library/react';

import { DatasetImport } from '../../../core/datasets/dataset.interface';
import { useLocalStorageDatasetImport } from './use-local-storage-dataset-import.hook';

// Mock localStorage
const mockLocalStorage = (() => {
    let store: Record<string, string> = {};

    return {
        getItem: jest.fn((key: string) => store[key] || null),
        setItem: jest.fn((key: string, value: string) => {
            store[key] = value;
        }),
        removeItem: jest.fn((key: string) => {
            delete store[key];
        }),
        clear: jest.fn(() => {
            store = {};
        }),
    };
})();

Object.defineProperty(window, 'localStorage', {
    value: mockLocalStorage,
});

interface TestDatasetImport extends DatasetImport {
    id: string;
    name: string;
    status: string;
    order?: number;
}

const STORAGE_KEY = 'test-dataset-imports';

const createTestItem = (id: string, name: string, status: string, order?: number): TestDatasetImport => ({
    id,
    name,
    status,
    order,
});

describe('useLocalStorageDatasetImport - putLsDatasetImport order preservation', () => {
    beforeEach(() => {
        mockLocalStorage.clear();
        jest.clearAllMocks();
    });

    it('should preserve order when adding new items and updating existing ones', () => {
        const { result } = renderHook(() => useLocalStorageDatasetImport<TestDatasetImport>(STORAGE_KEY));

        // Start with empty state
        expect(result.current.lsDatasetImports).toEqual([]);

        // Add first item to empty list
        act(() => {
            result.current.putLsDatasetImport(createTestItem('1', 'Dataset A', 'uploading'));
        });
        expect(result.current.lsDatasetImports?.map(item => item.id)).toEqual(['1']);

        // Add second item - should be appended
        act(() => {
            result.current.putLsDatasetImport(createTestItem('2', 'Dataset B', 'uploading'));
        });
        expect(result.current.lsDatasetImports?.map(item => item.id)).toEqual(['1', '2']);

        // Update first item - should stay in same position
        act(() => {
            result.current.putLsDatasetImport(createTestItem('1', 'Dataset A', 'processing'));
        });
        expect(result.current.lsDatasetImports?.map(item => item.id)).toEqual(['1', '2']);
        expect(result.current.lsDatasetImports?.[0].status).toBe('processing');

        // Add third item - should be appended at end
        act(() => {
            result.current.putLsDatasetImport(createTestItem('3', 'Dataset C', 'uploading'));
        });
        expect(result.current.lsDatasetImports?.map(item => item.id)).toEqual(['1', '2', '3']);

        // Update middle item - should stay in same position
        act(() => {
            result.current.putLsDatasetImport(createTestItem('2', 'Dataset B', 'completed'));
        });
        expect(result.current.lsDatasetImports?.map(item => item.id)).toEqual(['1', '2', '3']);
        expect(result.current.lsDatasetImports?.[1].status).toBe('completed');

        // Update last item - should stay in same position
        act(() => {
            result.current.putLsDatasetImport(createTestItem('3', 'Dataset C', 'failed'));
        });
        expect(result.current.lsDatasetImports?.map(item => item.id)).toEqual(['1', '2', '3']);
        expect(result.current.lsDatasetImports?.[2].status).toBe('failed');

        // Add fourth item - should be appended at end
        act(() => {
            result.current.putLsDatasetImport(createTestItem('4', 'Dataset D', 'uploading'));
        });
        expect(result.current.lsDatasetImports?.map(item => item.id)).toEqual(['1', '2', '3', '4']);

        // Final verification of all statuses
        expect(result.current.lsDatasetImports?.[0].status).toBe('processing');
        expect(result.current.lsDatasetImports?.[1].status).toBe('completed');
        expect(result.current.lsDatasetImports?.[2].status).toBe('failed');
        expect(result.current.lsDatasetImports?.[3].status).toBe('uploading');
    });
});
