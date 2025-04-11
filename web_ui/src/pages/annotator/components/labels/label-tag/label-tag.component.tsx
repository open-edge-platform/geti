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

import { Flex, Tooltip, TooltipTrigger } from '@adobe/react-spectrum';

import { Label } from '../../../../../core/labels/label.interface';
import { ActionElement } from '../../../../../shared/components/action-element/action-element.component';
import { LabelColorThumb } from '../../../../../shared/components/label-color-thumb/label-color-thumb.component';

interface LabelTagProps {
    id?: string;
    label: Label;
    onClick?: () => void;
    isPointer?: boolean;
}

export const LabelTag = ({ id, label, onClick, isPointer }: LabelTagProps): JSX.Element => {
    return (
        <Flex alignItems='center' gap='size-75'>
            <LabelColorThumb label={label} size={7} id={`${id}-color`} />

            <TooltipTrigger>
                <ActionElement
                    id={id}
                    isTruncated
                    onPress={onClick}
                    maxWidth={'size-2400'}
                    UNSAFE_style={{ cursor: isPointer ? 'pointer' : 'auto' }}
                >
                    {label.name}
                </ActionElement>
                <Tooltip>{label.name}</Tooltip>
            </TooltipTrigger>
        </Flex>
    );
};
