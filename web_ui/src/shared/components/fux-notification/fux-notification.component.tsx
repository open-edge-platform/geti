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

import { ComponentProps, MutableRefObject, ReactNode } from 'react';

import { Divider, Flex, Text } from '@adobe/react-spectrum';
import { Popover } from '@react-spectrum/overlays';
import isFunction from 'lodash/isFunction';

import { Close } from '../../../assets/icons';
import { openNewTab } from '../../utils';
import { Button } from '../button/button.component';
import { CustomPopover } from '../custom-popover/custom-popover.component';
import { QuietActionButton } from '../quiet-button/quiet-action-button.component';

import classes from './fux-notification.module.scss';

interface CustomPopoverProps extends Omit<ComponentProps<typeof Popover>, 'triggerRef' | 'children'> {
    docUrl?: string;
    children: ReactNode;
    triggerRef: MutableRefObject<null>;
    onClose?: () => void;
}

export const FuxNotification = ({ docUrl, placement, triggerRef, state, onClose, children }: CustomPopoverProps) => {
    return (
        <CustomPopover
            ref={triggerRef}
            hideArrow={false}
            placement={placement}
            state={state}
            UNSAFE_className={classes.container}
            isKeyboardDismissDisabled
        >
            <Flex direction={'row'} gap={'size-200'} alignItems={'center'}>
                <Text order={1}>{children}</Text>

                {docUrl && (
                    <Button
                        order={2}
                        variant='primary'
                        UNSAFE_style={{ border: 'none' }}
                        onPress={() => openNewTab(docUrl)}
                    >
                        Learn more
                    </Button>
                )}

                <Divider order={3} orientation='vertical' size='S' UNSAFE_className={classes.divider} />

                <QuietActionButton
                    order={4}
                    onPress={() => {
                        state.close();
                        isFunction(onClose) && onClose();
                    }}
                    aria-label={'close first user experience notification'}
                    UNSAFE_className={classes.close}
                >
                    <Close />
                </QuietActionButton>
            </Flex>
        </CustomPopover>
    );
};
