// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { CSSProperties } from 'react';

import { SortDirection } from '../../../core/shared/query-parameters';

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
