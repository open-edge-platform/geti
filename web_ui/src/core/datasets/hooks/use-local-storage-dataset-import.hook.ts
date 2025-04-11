// INTEL CONFIDENTIAL
//
// Copyright (C) 2022 Intel Corporation
//
// This software and the related documents are Intel copyrighted materials, and your use of them is governed by
// the express license under which they were provided to you ("License"). Unless the License provides otherwise,
// you may not use, modify, copy, publish, distribute, disclose or transmit this software or the related documents
// without Intel's prior written permission.
//
// This software and the related documents are provided as is, with no express or implied warranties,
// other than those that are expressly stated in the License.

import { useLocalStorage } from 'usehooks-ts';

import { getParsedLocalStorage, hasDifferentId, hasEqualId } from '../../../shared/utils';
import { DatasetImport } from '../dataset.interface';

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
