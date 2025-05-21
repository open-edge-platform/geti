// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { motion, Variants } from 'framer-motion';

type Sizes = 'S' | 'M';
type ColorVariant = 'dark' | 'light' | 'blue';

interface ThreeDotsFlashingProps {
    variant?: ColorVariant;
    size?: Sizes;
    className?: string;
}

const DOT_COLORS: Record<ColorVariant, string> = {
    dark: 'var(--spectrum-global-color-gray-800)',
    light: 'var(--spectrum-global-color-gray-50)',
    blue: 'var(--spectrum-global-color-gray-800)',
};

const DOT_SIZES: Record<Sizes, string> = {
    S: 'var(--spectrum-global-dimension-size-25)',
    M: 'var(--spectrum-global-dimension-size-50)',
};

export const ThreeDotsFlashing = ({ variant = 'dark', size = 'M', className }: ThreeDotsFlashingProps): JSX.Element => {
    const dotColor = DOT_COLORS[variant];
    const dotSize = DOT_SIZES[size];

    const dotVariants: Variants = {
        pulse: (i: number) => ({
            scale: [1, 1.4, 1],
            transition: {
                duration: 1.1,
                repeat: Infinity,
                ease: 'easeInOut',
                delay: i * 0.2,
            },
        }),
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
                    custom={i}
                    variants={dotVariants}
                    animate='pulse'
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
