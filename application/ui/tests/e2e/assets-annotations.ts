// Copyright (C) 2025-2026 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

import { Rect } from '@/api/types';

export const ANNOTATIONS_TO_DRAW_PER_ASSET: Record<string, { shape: Rect; label: string }[]> = {
    '1': [
        {
            shape: {
                type: 'rectangle',
                x: 382,
                y: 170,
                width: 224,
                height: 215,
            },
            label: 'minifig',
        },
        {
            shape: {
                type: 'rectangle',
                x: 128,
                y: 135,
                width: 810,
                height: 510,
            },
            label: 'car',
        },
    ],
    '2': [
        {
            shape: {
                type: 'rectangle',
                x: 406,
                y: 111,
                width: 154,
                height: 280,
            },
            label: 'minifig',
        },
        {
            shape: {
                type: 'rectangle',
                x: 364,
                y: 220,
                width: 302,
                height: 309,
            },
            label: 'motorbike',
        },
    ],
    '3': [
        {
            shape: {
                type: 'rectangle',
                x: 376,
                y: 251,
                width: 208,
                height: 356,
            },
            label: 'minifig',
        },
        {
            shape: {
                type: 'rectangle',
                x: 70,
                y: 17,
                width: 134,
                height: 260,
            },
            label: 'minifig',
        },
        {
            shape: {
                type: 'rectangle',
                x: 139,
                y: 85,
                width: 901,
                height: 434,
            },
            label: 'car',
        },
    ],
    '4': [
        {
            shape: {
                type: 'rectangle',
                x: 246,
                y: 257,
                width: 546,
                height: 266,
            },
            label: 'motorbike',
        },
        {
            shape: {
                type: 'rectangle',
                x: 397,
                y: 178,
                width: 225,
                height: 291,
            },
            label: 'minifig',
        },
    ],
    '5': [
        {
            shape: {
                type: 'rectangle',
                x: 255,
                y: 99,
                width: 620,
                height: 539,
            },
            label: 'car',
        },
        {
            shape: {
                type: 'rectangle',
                x: 457,
                y: 243,
                width: 169,
                height: 122,
            },
            label: 'minifig',
        },
    ],
    '6': [
        {
            shape: {
                type: 'rectangle',
                x: 392,
                y: 221,
                width: 362,
                height: 284,
            },
            label: 'motorbike',
        },
        {
            shape: {
                type: 'rectangle',
                x: 505,
                y: 180,
                width: 154,
                height: 227,
            },
            label: 'minifig',
        },
    ],
    '7': [
        {
            shape: {
                type: 'rectangle',
                x: 279,
                y: 162,
                width: 673,
                height: 443,
            },
            label: 'car',
        },
        {
            shape: {
                type: 'rectangle',
                x: 547,
                y: 270,
                width: 141,
                height: 123,
            },
            label: 'minifig',
        },
    ],
    '8': [
        {
            shape: {
                type: 'rectangle',
                x: 340,
                y: 314,
                width: 551,
                height: 319,
            },
            label: 'motorbike',
        },
        {
            shape: {
                type: 'rectangle',
                x: 149,
                y: 303,
                width: 202,
                height: 323,
            },
            label: 'minifig',
        },
    ],
    '9': [
        {
            shape: {
                type: 'rectangle',
                x: 222,
                y: 215,
                width: 669,
                height: 342,
            },
            label: 'car',
        },
        {
            shape: {
                type: 'rectangle',
                x: 536,
                y: 248,
                width: 114,
                height: 146,
            },
            label: 'minifig',
        },
    ],
    '10': [
        {
            shape: {
                type: 'rectangle',
                x: 226,
                y: 152,
                width: 681,
                height: 525,
            },
            label: 'motorbike',
        },
    ],
};
