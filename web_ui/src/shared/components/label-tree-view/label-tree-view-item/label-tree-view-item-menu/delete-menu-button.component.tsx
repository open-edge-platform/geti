// INTEL CONFIDENTIAL
//
// Copyright (C) 2022 Intel Corporation
//
// This software and the related documents are Intel copyrighted materials, and your use of them is governed by
// the express license under which they were provided to you ("License"). Unless the License provides otherwise,
// you may not use, modify, copy, publish, distribute, disclose or transmit this software or the related documents
// without Intel's prior written permission.
//
// This software and the related documents are provided as is, with no express or implied warranties,
// other than those that are expressly stated in the License.

import { Tooltip, TooltipTrigger } from '@adobe/react-spectrum';

import { Delete } from '../../../../../assets/icons';
import { QuietActionButton } from '../../../quiet-button/quiet-action-button.component';
import { MenuButtonProps } from './menu-button.interface';

export const DeleteMenuButton = ({ action, id }: MenuButtonProps): JSX.Element => {
    return (
        <TooltipTrigger placement={'bottom'}>
            <QuietActionButton
                key={'delete-button'}
                onPress={action}
                id={`${id}-delete-label-button`}
                data-testid={`${id}-delete-label-button`}
            >
                <Delete aria-label={'delete'} width={'16px'} height={'16px'} />
            </QuietActionButton>
            <Tooltip>Remove</Tooltip>
        </TooltipTrigger>
    );
};
