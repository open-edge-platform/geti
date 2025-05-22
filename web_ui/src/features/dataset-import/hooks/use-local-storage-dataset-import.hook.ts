// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { useLocalStorage } from 'usehooks-ts';

import { DatasetImport } from '../../../core/datasets/dataset.interface';
import { getParsedLocalStorage, hasDifferentId, hasEqualId } from '../../../shared/utils';

interface useLocalStorageDatasetImportProps<T> {
    lsDatasetImports: T[] | null;

    setLsDatasetImports: (items: T[]) => void;

    getLsDatasetImport: (id: string | undefined) => T | undefined;
    putLsDatasetImport: (item: T) => void;
    patchLsDatasetImport: (partialItem: Partial<T>) => void;
    deleteLsDatasetImport: (id: string | undefined) => void;
}

export const useLocalStorageDatasetImport = <T extends DatasetImport>(
    storageKey: string
): useLocalStorageDatasetImportProps<T> => {
    const [lsDatasetImports, setLsDatasetImports] = useLocalStorage<T[]>(storageKey, []);

    const getLsDatasetImport = (id: string | undefined): T | undefined => {
        if (!id) return;

        return getParsedLocalStorage<T[]>(storageKey)?.find(hasEqualId(id));
    };

    const putLsDatasetImport = (item: T): void => {
        setLsDatasetImports([...(getParsedLocalStorage(storageKey) as T[]).filter(hasDifferentId(item.id)), item]);
    };

    const patchLsDatasetImport = (partialItem: Partial<T>): void => {
        const item = getLsDatasetImport(partialItem.id);

        if (!item) return;

        putLsDatasetImport({ ...item, ...partialItem } as T);
    };

    const deleteLsDatasetImport = (id: string | undefined): void => {
        setLsDatasetImports([...lsDatasetImports.filter(hasDifferentId(id))]);
    };

    return {
        lsDatasetImports,

        setLsDatasetImports,

        getLsDatasetImport,
        putLsDatasetImport,
        patchLsDatasetImport,
        deleteLsDatasetImport,
    };
};
