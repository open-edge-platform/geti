// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { motion } from 'framer-motion';

import { ColorMode } from '../quiet-button/quiet-action-button.component';

type Sizes = 'S' | 'M';

interface ThreeDotsFlashingProps {
    mode?: ColorMode;
    size?: Sizes;
    className?: string;
}

const DOT_COLORS: Record<ColorMode, string> = {
    [ColorMode.DARK]: 'var(--spectrum-global-color-gray-800)',
    [ColorMode.LIGHT]: 'var(--spectrum-global-color-gray-50)',
    [ColorMode.BLUE]: 'var(--spectrum-global-color-gray-800)',
};

const DOT_SIZES: Record<Sizes, number> = {
    S: 8,
    M: 16,
};

export const ThreeDotsFlashing = ({
    mode = ColorMode.DARK,
    size = 'M',
    className,
}: ThreeDotsFlashingProps): JSX.Element => {
    const dotColor = DOT_COLORS[mode];
    const dotSize = DOT_SIZES[size];

    const dotVariants = {
        pulse: {
            scale: [1, 1.5, 1],
            transition: {
                duration: 1.2,
                repeat: Infinity,
                ease: 'easeInOut',
            },
        },
    };

    return (
        <div
            style={{ display: 'flex', gap: dotSize, alignItems: 'center', justifyContent: 'center' }}
            aria-label='three dots flashing animation'
            className={className}
        >
            {[0, 1, 2].map((i) => (
                <motion.div
                    key={i}
                    variants={dotVariants}
                    animate='pulse'
                    transition={{ delay: i * 0.2 }}
                    style={{
                        width: dotSize,
                        height: dotSize,
                        borderRadius: '50%',
                        background: dotColor,
                        willChange: 'transform',
                    }}
                />
            ))}
        </div>
    );
};
