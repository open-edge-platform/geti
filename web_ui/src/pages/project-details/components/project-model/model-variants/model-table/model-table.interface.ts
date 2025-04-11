// INTEL CONFIDENTIAL
//
// Copyright (C) 2024 Intel Corporation
//
// This software and the related documents are Intel copyrighted materials, and your use of them is governed by
// the express license under which they were provided to you ("License"). Unless the License provides otherwise,
// you may not use, modify, copy, publish, distribute, disclose or transmit this software or the related documents
// without Intel's prior written permission.
//
// This software and the related documents are provided as is, with no express or implied warranties,
// other than those that are expressly stated in the License.

import { StyleProps } from '@react-types/shared';
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
