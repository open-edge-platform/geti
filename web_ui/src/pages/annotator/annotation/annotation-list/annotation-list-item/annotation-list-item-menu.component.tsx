// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { Key } from 'react';

import { ActionButton, Flex, Item, Menu, MenuTrigger, Text } from '@geti/ui';
import { Delete, Edit, Invisible, Lock, MoreMenu, Unlock, Visible } from '@geti/ui/icons';

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
            <ActionButton
                isQuiet
                aria-label='Show actions'
                id={`annotation-list-item-${id}-menu`}
                isDisabled={isDisabled}
            >
                <MoreMenu className={isHidden ? classes.hiddenAnnotation : ''} />
            </ActionButton>
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
