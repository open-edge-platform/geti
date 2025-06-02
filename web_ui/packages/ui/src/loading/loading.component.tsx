// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { DimensionValue, Flex, ProgressCircle, View } from '@adobe/react-spectrum';
import { SpectrumProgressCircleProps } from '@react-types/progress';
import { Responsive } from '@react-types/shared/src/style';
import {
    BoxAlignmentStyleProps,
    StyleProps
} from '@react-types/shared';

interface LoadingProps extends SpectrumProgressCircleProps, StyleProps, BoxAlignmentStyleProps {
    mode?: 'inline' | 'fullscreen' | 'overlay';
    height?: Responsive<DimensionValue>;
    overlayHeight?: Responsive<DimensionValue>;
    id?: string;
    backgroundColor?: string;
    className?: string;
    paddingTop?: Responsive<DimensionValue>;
}

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
