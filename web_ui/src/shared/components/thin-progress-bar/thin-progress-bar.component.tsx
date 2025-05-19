// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { StyleProps, useStyleProps, View } from '@geti/ui';
import { ColorValue, DimensionValue } from '@geti/ui/src/dna';

export interface ThinProgressBarProps extends StyleProps {
    progress: number;
    completed?: boolean;
    color?: ColorValue;
    customColor?: string;
    trackColor?: ColorValue;
    size?: DimensionValue;
    id?: string;
}

export const ThinProgressBar = ({
    progress = 0,
    completed = false,
    size = 'size-50',
    color = 'blue-400',
    customColor = '',
    trackColor = 'gray-400',
    id,
    ...otherProps
}: ThinProgressBarProps): JSX.Element => {
    const { styleProps } = useStyleProps(otherProps);

    return (
        <View
            id={id}
            height={size}
            backgroundColor={trackColor}
            width='100%'
            borderRadius='small'
            UNSAFE_style={{ ...styleProps.style }}
        >
            <View
                height={size}
                backgroundColor={customColor ? undefined : color}
                width={completed ? '100%' : `${progress}%`}
                borderRadius='regular'
                UNSAFE_style={{ backgroundColor: customColor }}
                data-testid='thin-progress-bar'
            />
        </View>
    );
};
