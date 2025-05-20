// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { View, ViewProps } from '@react-spectrum/view';
import { StyleProps } from '@react-types/shared';

export interface ColorThumbProps extends StyleProps {
    color: string;
    size?: number;
    borderRadius?: ViewProps<5>['borderRadius'];
}

export const ColorThumb = ({ color, size = 10, ...viewProps }: ColorThumbProps): JSX.Element => {
    return (
        <View
            width={size}
            minWidth={size}
            height={size}
            borderRadius={'small'}
            UNSAFE_style={{
                backgroundColor: color,
            }}
            {...viewProps}
        />
    );
};
