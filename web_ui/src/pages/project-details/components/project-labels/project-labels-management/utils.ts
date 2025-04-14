// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

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
