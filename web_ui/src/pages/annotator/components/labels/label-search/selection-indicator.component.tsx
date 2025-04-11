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

import { FC, PropsWithChildren } from 'react';

import { dimensionValue } from '@react-spectrum/utils';

import { AcceptSmall, Add, CloseSmall } from '../../../../../assets/icons';
import { COLOR_MODE } from '../../../../../assets/icons/color-mode.enum';

const Wrapper: FC<PropsWithChildren & { ariaLabel?: string }> = ({ children, ariaLabel }) => {
    return (
        <div
            aria-label={ariaLabel}
            data-testid={'selection-suffix-id'}
            id={'selection-suffix-id'}
            style={{ width: dimensionValue('size-225'), height: dimensionValue('size-225') }}
        >
            {children}
        </div>
    );
};

export const SelectionIndicator = ({
    isHovered,
    isSelected,
}: {
    isHovered: boolean;
    isSelected: boolean;
}): JSX.Element => {
    if (isSelected) {
        if (isHovered) {
            return (
                <Wrapper ariaLabel={'Unassign label'}>
                    <CloseSmall color={COLOR_MODE.NEGATIVE} />
                </Wrapper>
            );
        }

        return (
            <Wrapper ariaLabel={'Assigned label'}>
                <AcceptSmall color={COLOR_MODE.POSITIVE} />
            </Wrapper>
        );
    } else {
        if (isHovered) {
            return (
                <Wrapper ariaLabel={'Assign label'}>
                    <Add />
                </Wrapper>
            );
        }

        return <Wrapper />;
    }
};
