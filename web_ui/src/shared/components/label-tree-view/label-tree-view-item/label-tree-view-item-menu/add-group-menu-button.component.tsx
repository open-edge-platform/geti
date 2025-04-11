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

import { AddGroup } from '../../../../../assets/icons';
import { QuietActionButton } from '../../../quiet-button/quiet-action-button.component';
import { MenuButtonProps } from './menu-button.interface';

export const AddGroupMenuButton = ({ action, id }: MenuButtonProps): JSX.Element => {
    const elementId = `${id}-add-child-group-button`;

    return (
        <TooltipTrigger placement={'bottom'}>
            <QuietActionButton
                key={elementId}
                onPress={action}
                id={elementId}
                data-testid={elementId}
                aria-label={'add child group button'}
            >
                <AddGroup aria-label={'add child'} width={'16px'} height={'16px'} />
            </QuietActionButton>
            <Tooltip>Add new group</Tooltip>
        </TooltipTrigger>
    );
};
