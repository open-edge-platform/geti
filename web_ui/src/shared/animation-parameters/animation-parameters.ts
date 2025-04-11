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

import { Variants } from 'framer-motion';

export enum AnimationDirections {
    MOVE_RIGHT = 1,
    MOVE_LEFT = -1,
}

type AnimationParametersKeys =
    | 'ANIMATE_ELEMENT_WITH_JUMP'
    | 'ANIMATE_LIST'
    | 'SLIDER'
    | 'IMAGE_HOVER'
    | 'ANIMATE_NOTIFICATION'
    | 'FADE_ITEM'
    | 'FADE_ITEM_SLOW';

export const ANIMATION_PARAMETERS: Record<AnimationParametersKeys, Variants> = {
    ANIMATE_ELEMENT_WITH_JUMP: {
        hidden: {
            opacity: 0,
            y: -50,
        },
        visible: {
            opacity: 1,
            y: 0,
            transition: {
                duration: 0.5,
            },
        },
        exit: {
            opacity: 0,
            y: -50,
        },
    },
    ANIMATE_LIST: {
        hidden: {
            opacity: 0,
        },
        visible: (i: number) => ({
            opacity: 1,
            transition: {
                delay: i * 0.1,
                duration: 0.35,
            },
        }),
    },
    IMAGE_HOVER: {
        hover: {
            scale: 1.1,
        },
    },
    SLIDER: {
        hidden: (direction: number) => ({
            x: direction > 0 ? -300 : 300,
            opacity: 0,
        }),
        visible: {
            x: 0,
            opacity: 1,
            transition: {
                duration: 0.5,
                easings: 'easeOut',
                x: {
                    type: 'spring',
                    stiffness: 100,
                    damping: 15,
                },
            },
        },
        exit: (direction: number) => ({
            x: direction < 0 ? -300 : 300,
            opacity: 0,
        }),
    },
    ANIMATE_NOTIFICATION: {
        hidden: {
            y: 100,
            opacity: 0,
        },
        visible: {
            y: 0,
            opacity: 1,
            transition: {
                duration: 0.3,
            },
        },
    },
    FADE_ITEM: {
        hidden: {
            opacity: 0,
        },
        visible: {
            opacity: 1,
            transition: {
                duration: 0.3,
            },
        },
        exit: {
            opacity: 0,
            transition: {
                duration: 0.2,
            },
        },
    },
    FADE_ITEM_SLOW: {
        hidden: {
            opacity: 0,
        },
        visible: {
            opacity: 1,
            transition: {
                duration: 1,
            },
        },
        exit: {
            opacity: 0,
            transition: {
                duration: 0.1,
            },
        },
    },
};
