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

import { Key } from 'react';

import { Flex, Item, Menu, MenuTrigger, Text } from '@adobe/react-spectrum';

import { Delete, Edit, Invisible, Lock, MoreMenu, Unlock, Visible } from '../../../../../assets/icons';
import { QuietActionButton } from '../../../../../shared/components/quiet-button/quiet-action-button.component';

import classes from './annotation-list-item.module.scss';

enum MENU_ACTIONS {
    HIDE = 'hide',
    SHOW = 'show',
    REMOVE = 'remove',
    LOCK = 'lock',
    UNLOCK = 'unlock',
    EDIT_LABELS = 'edit_labels',
}

interface AnnotationListItemMenuProps {
    id: string;
    isHidden: boolean;
    isLocked: boolean;
    isDisabled: boolean;
    hide: () => void;
    show: () => void;
    remove: () => void;
    toggleLock: () => void;
    editLabels: () => void;
}

export const AnnotationListItemMenu = ({
    id,
    isHidden,
    isLocked,
    isDisabled,
    hide,
    show,
    toggleLock,
    remove,
    editLabels,
}: AnnotationListItemMenuProps): JSX.Element => {
    const onAction = (key: Key) => {
        switch (key) {
            case MENU_ACTIONS.HIDE: {
                hide();
                break;
            }
            case MENU_ACTIONS.SHOW: {
                show();
                break;
            }
            case MENU_ACTIONS.REMOVE: {
                remove();
                break;
            }
            case MENU_ACTIONS.LOCK: {
                toggleLock();
                break;
            }
            case MENU_ACTIONS.UNLOCK: {
                toggleLock();
                break;
            }
            case MENU_ACTIONS.EDIT_LABELS: {
                editLabels();
                break;
            }
        }
    };

    const disabledKeys = isLocked ? [MENU_ACTIONS.REMOVE] : [];

    return (
        <MenuTrigger>
            <QuietActionButton aria-label='Show actions' id={`annotation-list-item-${id}-menu`} isDisabled={isDisabled}>
                <MoreMenu className={isHidden ? classes.hiddenAnnotation : ''} />
            </QuietActionButton>
            <Menu onAction={onAction} disabledKeys={disabledKeys}>
                {isHidden ? (
                    <Item key={MENU_ACTIONS.SHOW} textValue='Show'>
                        <Text>
                            <Flex alignItems={'center'} justifyContent={'space-between'} gap={'size-300'}>
                                <Flex alignItems={'center'} gap={'size-125'}>
                                    <Visible />
                                    <Text>Show</Text>
                                </Flex>
                            </Flex>
                        </Text>
                    </Item>
                ) : (
                    <Item key={MENU_ACTIONS.HIDE} textValue='Hide'>
                        <Text>
                            <Flex alignItems={'center'} justifyContent={'space-between'} gap={'size-300'}>
                                <Flex alignItems={'center'} gap={'size-125'}>
                                    <Invisible />
                                    <Text>Hide</Text>
                                </Flex>
                            </Flex>
                        </Text>
                    </Item>
                )}
                {isLocked ? (
                    <Item key={MENU_ACTIONS.UNLOCK} textValue='Unlock'>
                        <Text>
                            <Flex alignItems={'center'} justifyContent={'space-between'} gap={'size-300'}>
                                <Flex alignItems={'center'} gap={'size-125'}>
                                    <Unlock />
                                    <Text>Unlock</Text>
                                </Flex>
                            </Flex>
                        </Text>
                    </Item>
                ) : (
                    <Item key={MENU_ACTIONS.LOCK} textValue='Lock'>
                        <Text>
                            <Flex alignItems={'center'} justifyContent={'space-between'} gap={'size-300'}>
                                <Flex alignItems={'center'} gap={'size-125'}>
                                    <Lock />
                                    <Text>Lock</Text>
                                </Flex>
                            </Flex>
                        </Text>
                    </Item>
                )}
                <Item key={MENU_ACTIONS.REMOVE} textValue='Remove'>
                    <Text>
                        <Flex alignItems={'center'} justifyContent={'space-between'} gap={'size-300'}>
                            <Flex alignItems={'center'} gap={'size-125'}>
                                <Delete />
                                <Text>Remove</Text>
                            </Flex>
                        </Flex>
                    </Text>
                </Item>
                <Item key={MENU_ACTIONS.EDIT_LABELS} textValue='Edit labels'>
                    <Text>
                        <Flex alignItems={'center'} justifyContent={'space-between'} gap={'size-300'}>
                            <Flex alignItems={'center'} gap={'size-125'}>
                                <Edit />
                                <Text>Edit labels</Text>
                            </Flex>
                        </Flex>
                    </Text>
                </Item>
            </Menu>
        </MenuTrigger>
    );
};
