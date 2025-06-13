// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { CSSProperties } from 'react';

import { Flex, ProgressCircle, View } from '@adobe/react-spectrum';
import { SpectrumProgressCircleProps } from '@react-types/progress';
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
     * CSS styles for the container.
     * For inline mode: styles the Flex container
     * For overlay modes: styles the overlay View container
     */
    style?: CSSProperties;

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
    style = {},
    className,
    ...rest
}: LoadingProps): JSX.Element => {
    if (mode === 'inline') {
        return (
            <Flex alignItems={'center'} justifyContent={'center'} UNSAFE_style={style} UNSAFE_className={className}>
                <ProgressCircle aria-label={'Loading...'} isIndeterminate size={size} {...rest} />
            </Flex>
        );
    }

    // Determine CSS classes based on mode
    const overlayClassName = clsx(classes.overlay, mode === 'overlay' ? classes.modal : classes.fullscreen, className);

    return (
        <View UNSAFE_style={style} UNSAFE_className={overlayClassName}>
            <ProgressCircle aria-label={'Loading...'} isIndeterminate size={size} {...rest} />
        </View>
    );
};
