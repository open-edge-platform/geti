// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

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
