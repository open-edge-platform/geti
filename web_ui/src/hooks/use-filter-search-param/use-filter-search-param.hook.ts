// INTEL CONFIDENTIAL
//
// Copyright (C) 2023 Intel Corporation
//
// This software and the related documents are Intel copyrighted materials, and your use of them is governed by
// the express license under which they were provided to you ("License"). Unless the License provides otherwise,
// you may not use, modify, copy, publish, distribute, disclose or transmit this software or the related documents
// without Intel's prior written permission.
//
// This software and the related documents are provided as is, with no express or implied warranties,
// other than those that are expressly stated in the License.

import { useCallback, useMemo } from 'react';

import { useSearchParams } from 'react-router-dom';
import { parse, stringify } from 'zipson/lib';

// The `decodeFromBinary` and `encodeToBinary` functions are taken from,
// https://tanstack.com/router/v1/docs/guide/custom-search-param-serialization#using-zipson
// These functions make sure that the strings generated from `stringify` are properly encoded,
// even when `atob` or `btoa` do not guarantee to work with UTF8 characters
const decodeFromBinary = (str: string): string => {
    return decodeURIComponent(
        Array.prototype.map
            .call(atob(str), function (c) {
                return '%' + ('00' + c.charCodeAt(0).toString(16)).slice(-2);
            })
            .join('')
    );
};

const encodeToBinary = (str: string): string => {
    return btoa(
        encodeURIComponent(str).replace(/%([0-9A-F]{2})/g, function (_match, p1) {
            return String.fromCharCode(parseInt(p1, 16));
        })
    );
};

export const encodeFilterSearchParam = <SearchType>(filterSearch: SearchType): string => {
    return encodeToBinary(encodeURIComponent(stringify(filterSearch)));
};

export const getFilterParam = <T>(filterParam: string): T => {
    try {
        // This may fail if the user manually changes the filter parameter in the url,
        // in that case we ignore the filter
        return (parse(decodeURIComponent(decodeFromBinary(filterParam ?? ''))) ?? {}) as T;
    } catch {
        return {} as T;
    }
};

type UseFilterSearchParam<SearchType> = [SearchType, (options: SearchType) => void];

export const useFilterSearchParam = <SearchType>(
    name: string,
    isActiveSet = false
): UseFilterSearchParam<SearchType> => {
    const [searchParams, setSearchParams] = useSearchParams();
    const filterParam = searchParams.get(name) ?? '';

    const options: SearchType = useMemo(() => {
        return getFilterParam(filterParam);
    }, [filterParam]);

    const setOptions = useCallback(
        (rules: SearchType) => {
            searchParams.set(name, encodeFilterSearchParam(rules));
            isActiveSet && searchParams.delete('active');
            setSearchParams(searchParams);
        },
        [isActiveSet, name, searchParams, setSearchParams]
    );

    return [options, setOptions];
};
