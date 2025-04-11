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
