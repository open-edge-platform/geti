// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { type ColumnSize, type StyleProps } from '@geti/ui';

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
