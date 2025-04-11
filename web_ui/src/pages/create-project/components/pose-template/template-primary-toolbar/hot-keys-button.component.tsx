// INTEL CONFIDENTIAL
//
// Copyright (C) 2025 Intel Corporation
//
// This software and the related documents are Intel copyrighted materials, and your use of them is governed by
// the express license under which they were provided to you ("License"). Unless the License provides otherwise,
// you may not use, modify, copy, publish, distribute, disclose or transmit this software or the related documents
// without Intel's prior written permission.
//
// This software and the related documents are provided as is, with no express or implied warranties,
// other than those that are expressly stated in the License.

import { ReactNode } from 'react';

import { Content, Dialog, DialogTrigger, Divider, Flex, Keyboard, Text, View } from '@adobe/react-spectrum';

import { Hotkeys, LeftClick, RightClick } from '../../../../../assets/icons';
import { QuietActionButton } from '../../../../../shared/components/quiet-button/quiet-action-button.component';

import classes from './hot-keys-button.module.scss';

interface HotKeysItemProps {
    text: string;
    children: ReactNode;
}
const HotKeysItem = ({ text, children }: HotKeysItemProps) => {
    return (
        <Flex
            gap={'size-100'}
            alignItems={'center'}
            marginBottom={'size-150'}
            UNSAFE_style={{
                color: 'var(--spectrum-global-color-gray-700)',
                fontSize: 'var(--spectrum-global-dimension-font-size-75)',
                fontWeight: 'var(--spectrum-global-font-weight-bold)',
            }}
        >
            <Text width={'42%'}>{text}</Text>
            <Keyboard width={'50%'}>{children}</Keyboard>
        </Flex>
    );
};
export const HotKeysButton = (): JSX.Element => {
    return (
        <DialogTrigger type={'popover'} mobileType={'modal'} placement={'right top'} hideArrow>
            <QuietActionButton aria-label='Show dialog with hotkeys'>
                <Hotkeys />
            </QuietActionButton>
            <Dialog size='M'>
                <Content>
                    <HotKeysItem text='Create node'>
                        <LeftClick />
                    </HotKeysItem>
                    <HotKeysItem text='Create edge'>
                        <Flex gap={'size-100'}>
                            <View UNSAFE_className={classes.keyContainer} maxHeight={'size-225'}>
                                SHIFT
                            </View>
                            <Text>+</Text>
                            <View>
                                <LeftClick />
                            </View>
                            <Text>on node and drag to another node</Text>
                        </Flex>
                    </HotKeysItem>

                    <Divider size={'S'} marginBottom={'size-150'} />
                    <HotKeysItem text='Remove node or edge'>
                        <View UNSAFE_className={classes.keyContainer}>DEL</View>
                    </HotKeysItem>

                    <Divider size={'S'} marginBottom={'size-150'} />
                    <HotKeysItem text='Display the context menu'>
                        <RightClick />
                    </HotKeysItem>
                </Content>
            </Dialog>
        </DialogTrigger>
    );
};
