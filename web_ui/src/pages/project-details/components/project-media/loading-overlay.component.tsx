// INTEL CONFIDENTIAL
//
// Copyright (C) 2021 Intel Corporation
//
// This software and the related documents are Intel copyrighted materials, and your use of them is governed by
// the express license under which they were provided to you ("License"). Unless the License provides otherwise,
// you may not use, modify, copy, publish, distribute, disclose or transmit this software or the related documents
// without Intel's prior written permission.
//
// This software and the related documents are provided as is, with no express or implied warranties,
// other than those that are expressly stated in the License.

import { ComponentProps } from 'react';

import { DimensionValue, Flex, ProgressCircle } from '@adobe/react-spectrum';
import { View } from '@react-spectrum/view';
import { BackgroundColorValue, BoxAlignmentStyleProps, Responsive, StyleProps } from '@react-types/shared';

interface LoadingOverlayProps extends StyleProps, BoxAlignmentStyleProps {
    id?: string;
    size?: ComponentProps<typeof ProgressCircle>['size'];
    visible: boolean;
    className?: string;
    fetchingNextPage?: boolean;
    paddingTop?: Responsive<DimensionValue> | undefined;
    backgroundColor?: Responsive<BackgroundColorValue>;
}

export const LoadingOverlay = ({
    id,
    visible,
    className,
    height,
    size = 'L',
    position = 'absolute',
    alignItems = 'center',
    marginTop,
    paddingTop,
    fetchingNextPage,
    backgroundColor = 'gray-50',
}: LoadingOverlayProps): JSX.Element => {
    if (!visible) {
        return <></>;
    }

    return (
        <View
            id={id}
            zIndex={20}
            height={height}
            position={position}
            marginTop={marginTop}
            paddingTop={paddingTop}
            // If we're loading the whole container we want the overlay to occupy everything.
            // But if we're just fetching the next page, we want the overlay to just cover a portion
            // of the bottom part, hence these 2 conditions below with top/bottom.
            top={fetchingNextPage ? undefined : 0}
            bottom={fetchingNextPage ? 'size-100' : 0}
            left={0}
            right={0}
            backgroundColor={backgroundColor}
            UNSAFE_style={{ cursor: 'default' }}
            UNSAFE_className={className}
        >
            <Flex width='100%' height='100%' alignItems={alignItems} justifyContent='center'>
                <ProgressCircle size={size} isIndeterminate aria-label='Loading...' />
            </Flex>
        </View>
    );
};
