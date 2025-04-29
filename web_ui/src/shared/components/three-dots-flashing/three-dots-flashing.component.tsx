// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { CSSProperties } from 'react';

import clsx from 'clsx';

import { ColorMode } from '../quiet-button/quiet-action-button.component';

import classes from './three-dots-flashing.component.module.scss';

type Sizes = 'S' | 'M';

interface ThreeDotsFlashingProps {
    mode?: ColorMode;
    size?: Sizes;
    className?: string;
}

export const ThreeDotsFlashing = ({
    mode = ColorMode.DARK,
    size = 'M',
    className,
}: ThreeDotsFlashingProps): JSX.Element => {
    const colors: Record<ColorMode, CSSProperties> = {
        [ColorMode.DARK]: {
            '--bgColorStartAnimation': 'var(--spectrum-global-color-gray-800)',
            '--bgColorEndAnimation': 'var(--white-down)',
        } as CSSProperties,
        [ColorMode.LIGHT]: {
            '--bgColorStartAnimation': 'var(--spectrum-global-color-gray-50)',
            '--bgColorEndAnimation': 'var(--dark-down)',
        } as CSSProperties,
        [ColorMode.BLUE]: {
            '--bgColorStartAnimation': 'var(--spectrum-global-color-gray-800)',
            '--bgColorEndAnimation': 'var(--white-down)',
        } as CSSProperties,
    };

    const sizes: Record<Sizes, CSSProperties> = {
        S: {
            '--dotSize': 'var(--spectrum-global-dimension-size-25)',
        } as CSSProperties,
        M: {
            '--dotSize': 'var(--spectrum-global-dimension-size-50)',
        } as CSSProperties,
    };

    return (
        <div
            style={{ ...colors[mode], ...sizes[size] }}
            className={clsx(classes.flashingAnimation, className)}
            aria-label={'three dots flashing animation'}
        ></div>
    );
};
