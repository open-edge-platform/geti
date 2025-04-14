// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

export const selectAnchorPointLabel = (idx: number, isSelected: boolean, selectedAnchorIndexes: number[]): string => {
    if (isSelected) {
        return `Click to unselect, or press delete to remove point ${idx}`;
    }
    return selectedAnchorIndexes.length > 0 ? `Shift click to select point ${idx}` : `Click to select point ${idx}`;
};
