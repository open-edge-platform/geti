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

import { LabelTreeItem, LabelTreeLabelProps } from '../../../../../core/labels/label-tree-view.interface';
import { DISTINCT_COLORS, getHEXFormat } from '../../../../create-project/components/distinct-colors';

export const getAvailableColors = (flatItems: LabelTreeItem[] | undefined): string[] => {
    if (!flatItems) {
        return DISTINCT_COLORS;
    }

    const labels = flatItems.filter((item: LabelTreeItem) => 'color' in item) as LabelTreeLabelProps[];

    const usedColors = labels.map(({ color }) => getHEXFormat(color).toUpperCase());
    while (usedColors && usedColors.length >= DISTINCT_COLORS.length) {
        for (const color of DISTINCT_COLORS) {
            usedColors.splice(usedColors.indexOf(color), 1);
        }
    }

    return DISTINCT_COLORS.filter((color) => usedColors && !usedColors.includes(color));
};
