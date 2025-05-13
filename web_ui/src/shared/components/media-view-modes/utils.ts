// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

export enum ViewModes {
    LARGE = 'Large thumbnails',
    MEDIUM = 'Medium thumbnails',
    SMALL = 'Small thumbnails',
    DETAILS = 'Details',
}

export const INITIAL_VIEW_MODE = ViewModes.MEDIUM;
export const VIEW_MODE_LABEL = 'View mode';

export const VIEW_MODE_SETTINGS = {
    [ViewModes.SMALL]: { minItemSize: 112, gap: 4, maxColumns: 11 },
    [ViewModes.MEDIUM]: { minItemSize: 150, gap: 8, maxColumns: 8 },
    [ViewModes.LARGE]: { minItemSize: 300, gap: 12, maxColumns: 4 },
    [ViewModes.DETAILS]: { size: 81, gap: 0 },
};
