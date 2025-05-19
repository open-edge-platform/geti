// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { ComponentProps, MutableRefObject, ReactNode } from 'react';

import { Button, CustomPopover, Divider, Flex, Text } from '@geti/ui';
import { Popover } from '@react-spectrum/overlays';
import { isFunction } from 'lodash-es';

import { Close } from '../../../../../assets/icons';
import { openNewTab } from '../../../../utils';
import { QuietActionButton } from '../../../quiet-button/quiet-action-button.component';

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
