// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { Key, MutableRefObject, useEffect, useRef, useState } from 'react';

import { Flex, Item, Menu, Section, Text } from '@adobe/react-spectrum';
import { Overlay } from '@react-spectrum/overlays';
import { AnimatePresence, motion } from 'framer-motion';
import { isFunction } from 'lodash-es';
import { useOverlay } from 'react-aria';

import { ANIMATION_PARAMETERS } from '../../../../../shared/animation-parameters/animation-parameters';

import classes from './context-menu.module.scss';

export interface MenuPosition {
    top: number;
    left: number;
}

interface MenuItem {
    icon: JSX.Element;
    title: string;
    shortcut?: string;
}

interface MenuItems {
    id: string;
    children: MenuItem[];
}

export interface ContextMenuProps {
    isVisible: boolean;
    handleClose: () => void;
    handleMenuAction: (key: Key) => void;
    ariaLabel: string;
    menuItems: MenuItems[];
    menuPosition: MenuPosition;
    disabledKeys?: string[];
    getContextMenuPosition?: (contextHeight: number, contextWidth: number, menuPosition: MenuPosition) => MenuPosition;
}

export const ContextMenu = ({
    handleMenuAction,
    isVisible,
    handleClose,
    menuItems,
    ariaLabel,
    menuPosition,
    disabledKeys,
    getContextMenuPosition,
}: ContextMenuProps): JSX.Element => {
    const overlayRef = useRef(null);
    const viewRef = useRef<HTMLDivElement | null>(null);
    const [adjustedContextMenuPosition, setAdjustedContextMenuPosition] = useState<MenuPosition>(menuPosition);

    useOverlay(
        {
            isOpen: isVisible,
            isDismissable: true,
            shouldCloseOnBlur: false,
            onClose: handleClose,
        },
        viewRef
    );

    const handleAction = (key: Key) => {
        handleMenuAction(key);

        handleClose();
    };

    useEffect(() => {
        if (viewRef.current === null || !isFunction(getContextMenuPosition)) return;

        const newContextMenuPosition = getContextMenuPosition(
            viewRef.current.clientHeight,
            viewRef.current.clientWidth,
            menuPosition
        );

        setAdjustedContextMenuPosition(newContextMenuPosition);
        // eslint-disable-next-line react-hooks/exhaustive-deps
    }, [viewRef.current, menuPosition]);

    return (
        <AnimatePresence>
            <Overlay isOpen={isVisible} nodeRef={overlayRef as unknown as MutableRefObject<HTMLElement>}>
                <motion.div
                    variants={ANIMATION_PARAMETERS.FADE_ITEM}
                    initial={'hidden'}
                    exit={'exit'}
                    animate={'visible'}
                    className={classes.container}
                    ref={viewRef}
                    style={adjustedContextMenuPosition}
                >
                    <Menu
                        items={menuItems}
                        aria-label={ariaLabel}
                        onAction={handleAction}
                        disabledKeys={disabledKeys}
                        minWidth={'size-2400'}
                    >
                        {({ children }) => (
                            <Section items={children}>
                                {({ title, icon, shortcut }) => (
                                    <Item key={title} textValue={title} aria-label={title}>
                                        <Text>
                                            <Flex
                                                alignItems={'center'}
                                                justifyContent={'space-between'}
                                                gap={'size-300'}
                                            >
                                                <Flex alignItems={'center'} gap={'size-125'}>
                                                    {icon}
                                                    <Text>{title}</Text>
                                                </Flex>
                                                {shortcut && (
                                                    <Text UNSAFE_className={classes.shortcut}>
                                                        {shortcut.toUpperCase()}
                                                    </Text>
                                                )}
                                            </Flex>
                                        </Text>
                                    </Item>
                                )}
                            </Section>
                        )}
                    </Menu>
                </motion.div>
            </Overlay>
        </AnimatePresence>
    );
};
