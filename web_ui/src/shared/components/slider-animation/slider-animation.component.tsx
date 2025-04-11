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

import { CSSProperties, ReactNode } from 'react';

import { AnimatePresence, motion } from 'framer-motion';

import { ANIMATION_PARAMETERS } from '../../animation-parameters/animation-parameters';

interface SliderAnimationProps {
    children: ReactNode;
    animationDirection: number;
    style?: CSSProperties;
}

export const SliderAnimation = ({ children, animationDirection, style }: SliderAnimationProps): JSX.Element => (
    <AnimatePresence mode='wait'>
        <motion.div
            variants={ANIMATION_PARAMETERS.SLIDER}
            initial={'hidden'}
            animate={'visible'}
            exit={'exit'}
            custom={animationDirection}
            style={style}
        >
            {children}
        </motion.div>
    </AnimatePresence>
);
