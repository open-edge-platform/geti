// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { CSSProperties } from 'react';

import { DimensionValue, Flex, ProgressCircle, View } from '@adobe/react-spectrum';
import { SpectrumProgressCircleProps } from '@react-types/progress';
import { Responsive } from '@react-types/shared/src/style';
import { clsx } from 'clsx';

import classes from './loading.module.scss';

/**
 * Props for the Loading component.
 *
 * Extends Adobe Spectrum's ProgressCircle props to provide a flexible loading indicator
 * suitable for various use cases.
 */
interface LoadingProps extends SpectrumProgressCircleProps {
    /**
     * The display mode for the loading component.
     * - 'inline': Renders as an inline element without overlay positioning
     * - 'fullscreen': Renders as a full-screen overlay with default background
     * - 'overlay': Renders as a positioned overlay with modal background
     * @default 'fullscreen'
     */
    mode?: 'inline' | 'fullscreen' | 'overlay';

    /**
     * Height of the spinner container (not the overlay itself).
     * @default '100%'
     */
    height?: Responsive<DimensionValue>;

    /**
     * CSS styles for the overlay container.
     * This allows full control over positioning, dimensions, spacing, and appearance.
     */
    style?: CSSProperties;

    id?: string;
    className?: string;
}

/**
 * A flexible loading component that can display a progress circle in different modes.
 *
 * This component consolidates various loading patterns used throughout the application:
 * - Inline loading indicators
 * - Full-screen loading overlays
 * - Modal-style loading overlays
 *
 * The component automatically handles positioning, background colors, and accessibility
 * attributes based on the selected mode.
 *
 * @example
 * ```tsx
 * // Simple inline loading spinner
 * <Loading mode="inline" size="M" />
 *
 * // Full-screen overlay with custom background
 * <Loading mode="overlay" style={{ backgroundColor: "rgba(0,0,0,0.5)" }} />
 *
 * // Custom positioned overlay
 * <Loading mode="overlay" style={{
 *   top: 100,
 *   left: 50,
 *   width: 200,
 *   height: 200,
 *   backgroundColor: "white"
 * }} />
 *
 * // Conditional loading overlay
 * {isLoading && <Loading mode="overlay" />}
 * ```
 *
 * @param props - The component props
 * @returns A loading component with progress circle
 */
export const Loading = ({
    mode = 'fullscreen',
    size = 'L',
    height = '100%',
    style = {},
    id,
    className,
    ...rest
}: LoadingProps): JSX.Element => {
    const spinner = (
        <Flex alignItems={'center'} justifyContent={'center'} height={height}>
            <ProgressCircle aria-label={'Loading...'} isIndeterminate size={size} {...rest} />
        </Flex>
    );

    if (mode === 'inline') {
        return spinner;
    }

    // Determine CSS classes based on mode
    const overlayClassName = clsx(classes.overlay, mode === 'overlay' ? classes.modal : classes.fullscreen, className);

    return (
        <View id={id} data-testid={id} UNSAFE_style={style} UNSAFE_className={overlayClassName}>
            {spinner}
        </View>
    );
};
