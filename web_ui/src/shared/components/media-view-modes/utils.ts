// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { CSSProperties } from 'react';

export enum ViewModes {
    LARGE = 'Large thumbnails',
    MEDIUM = 'Medium thumbnails',
    SMALL = 'Small thumbnails',
    DETAILS = 'Details',
}

export const INITIAL_VIEW_MODE = ViewModes.MEDIUM;
export const VIEW_MODE_LABEL = 'View mode';

/*
 * minNumberOfCols is not used, but I leave it here for the documentation purpose.
 * */

export const VIEW_MODE_SETTINGS = {
    [ViewModes.SMALL]: {
        '--minWidth': 72,
        '--maxWidth': 128,
        '--gap': 4,
        '--modeFactor': 0.5,
        '--minNumberOfCols': 3,
    },
    [ViewModes.MEDIUM]: {
        '--minWidth': 96,
        '--maxWidth': 240,
        '--gap': 8,
        '--modeFactor': 0.6,
        '--minNumberOfCols': 2,
    },
    [ViewModes.LARGE]: {
        '--minWidth': 168,
        '--maxWidth': 320,
        '--gap': 12,
        '--modeFactor': 2,
        '--minNumberOfCols': 1,
    },
    [ViewModes.DETAILS]: {
        '--width': '64px',
        '--gap': '8px',
    },
} as Record<ViewModes, CSSProperties>;
