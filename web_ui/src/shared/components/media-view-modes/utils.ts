// INTEL CONFIDENTIAL
//
// Copyright (C) 2022 Intel Corporation
//
// This software and the related documents are Intel copyrighted materials, and your use of them is governed by
// the express license under which they were provided to you ("License"). Unless the License provides otherwise,
// you may not use, modify, copy, publish, distribute, disclose or transmit this software or the related documents
// without Intel's prior written permission.
//
// This software and the related documents are provided as is, with no express or implied warranties,
// other than those that are expressly stated in the License.

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
