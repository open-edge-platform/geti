// INTEL CONFIDENTIAL
//
// Copyright (C) 2021 Intel Corporation
//
// This software and the related documents are Intel copyrighted materials, and your use of them is governed by
// the express license under which they were provided to you ("License"). Unless the License provides otherwise,
// you may not use, modify, copy, publish, distribute, disclose or transmit this software or the related documents
// without Intel's prior written permission.
//
// This software and the related documents are provided as is, with no express or implied warranties,
// other than those that are expressly stated in the License.

import { CSSProperties } from 'react';

export type SortDirection = 'ASC' | 'DESC' | undefined;

export interface SortingOptions {
    sortBy: string | undefined;
    sortDirection: SortDirection | undefined;
}

export interface TableCellProps {
    // eslint-disable-next-line @typescript-eslint/no-explicit-any
    rowData: any;
    // eslint-disable-next-line @typescript-eslint/no-explicit-any
    cellData?: any;
    columnIndex: number;
    dataKey: string;
    isScrolling: boolean;
    rowIndex: number;
    isSubRow?: boolean;
    styles?: CSSProperties;
}

export interface SortingParams extends SortingOptions {
    sort: (props: SortingOptions) => void;
}
