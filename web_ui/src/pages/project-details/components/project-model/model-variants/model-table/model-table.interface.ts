// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { StyleProps } from '@geti/ui';
import { ColumnSize } from '@react-types/table';

export interface ModelTableColumns<T> {
    label: string;
    width: ColumnSize;
    align?: 'start' | 'center' | 'end';
    component: (props: T) => JSX.Element;
}

export interface ModelTableProps<T> extends StyleProps {
    data: T[];
    columns: ModelTableColumns<T>[];
}
