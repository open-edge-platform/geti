// INTEL CONFIDENTIAL
//
// Copyright (C) 2023 Intel Corporation
//
// This software and the related documents are Intel copyrighted materials, and your use of them is governed by
// the express license under which they were provided to you ("License"). Unless the License provides otherwise,
// you may not use, modify, copy, publish, distribute, disclose or transmit this software or the related documents
// without Intel's prior written permission.
//
// This software and the related documents are provided as is, with no express or implied warranties,
// other than those that are expressly stated in the License.

import { View } from '@adobe/react-spectrum';
import { BorderRadiusValue } from '@react-types/shared/src/dna';
import { Responsive } from '@react-types/shared/src/style';

import { ActionButton } from '../button/button.component';

interface ChangeColorButtonProps {
    size: 'S' | 'L';
    id: string;
    color: string | undefined;
    ariaLabelPrefix?: string;
    gridArea?: string;
}

export const ChangeColorButton = ({
    size,
    ariaLabelPrefix,
    id,
    color,
    gridArea,
}: ChangeColorButtonProps): JSX.Element => {
    const sizeParameters: { size: string; radius?: Responsive<BorderRadiusValue> } =
        size === 'L' ? { size: 'size-400', radius: 'small' } : { size: 'size-125' };

    return (
        <ActionButton
            id={id}
            data-testid={`${id}-button`}
            height={'fit-content'}
            isQuiet={false}
            aria-label={`${ariaLabelPrefix ? ariaLabelPrefix + ' ' : ''}Color picker button`}
            gridArea={gridArea}
        >
            <View
                width={sizeParameters.size}
                height={sizeParameters.size}
                minWidth={sizeParameters.size}
                borderRadius={sizeParameters.radius || undefined}
                margin={10}
                id={`${id}-selected-color`}
                UNSAFE_style={{ backgroundColor: color }}
            />
        </ActionButton>
    );
};
