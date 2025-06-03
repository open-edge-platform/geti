// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { DimensionValue, Flex, ProgressCircle, View } from '@adobe/react-spectrum';
import { SpectrumProgressCircleProps } from '@react-types/progress';
import { Responsive } from '@react-types/shared/src/style';
import {
    BoxAlignmentStyleProps,
    StyleProps
} from '@react-types/shared';

/**
 * Props for the Loading component.
 *
 * Extends Adobe Spectrum's ProgressCircle props along with styling and alignment props
 * to provide a flexible loading indicator suitable for various use cases.
 */
interface LoadingProps extends SpectrumProgressCircleProps, StyleProps, BoxAlignmentStyleProps {
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
     * Height of the overlay container when in fullscreen or overlay mode.
     * @default '100%'
     */
    overlayHeight?: Responsive<DimensionValue>;

    id?: string;
    backgroundColor?: string;
    className?: string;
    paddingTop?: Responsive<DimensionValue>;
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
 * <Loading mode="overlay" backgroundColor="rgba(0,0,0,0.5)" />
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
    overlayHeight = '100%',
    id,
    backgroundColor,
    className,
    alignItems = 'center',
    justifyContent = 'center',
    paddingTop,
    marginTop,
    left = 0,
    right = 0,
    top = 0,
    bottom = 0,
    ...rest
}: LoadingProps): JSX.Element => {
    const spinner = (
        <Flex alignItems={alignItems} justifyContent={justifyContent} height={height}>
            <ProgressCircle aria-label={'Loading...'} isIndeterminate size={size} {...rest} />
        </Flex>
    );

    if (mode === 'inline') {
        return spinner;
    }

    return (
        <View
            height={overlayHeight}
            position={'absolute'}
            left={left}
            right={right}
            top={top}
            bottom={bottom}
            zIndex={mode === 'overlay' ? 20 : undefined}
            paddingTop={paddingTop}
            marginTop={marginTop}
            id={id}
            data-testid={id}
            UNSAFE_style={{
                cursor: 'default',
                // Use modal overlay background for overlay mode, or custom/default background for fullscreen
                backgroundColor: backgroundColor || (
                    mode === 'overlay' ? 'var(--spectrum-alias-background-color-modal-overlay)' : 'gray-50'
                ),
            }}
            UNSAFE_className={className}
        >
            {spinner}
        </View>
    );
};
