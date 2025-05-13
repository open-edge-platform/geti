// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { Key, RefObject, useRef, useState } from 'react';

import { Item, Menu } from '@adobe/react-spectrum';
import { Button } from '@geti/ui';
import { useOverlayTriggerState } from '@react-stately/overlays';
import { isFunction } from 'lodash-es';

import { useEventListener } from '../../../../hooks/event-listener/event-listener.hook';
import { CustomPopover } from '../../../../shared/components/custom-popover/custom-popover.component';
import { MouseEvents } from '../../../../shared/mouse-events/mouse.interface';

interface MediaItemContextMenuProps {
    options: [string, () => void][];
    containerRef: RefObject<HTMLElement>;
}

export const MediaItemContextMenu = ({ options, containerRef }: MediaItemContextMenuProps): JSX.Element => {
    const menuTriggerRef = useRef(null);
    const menuOverlayState = useOverlayTriggerState({});
    const [menuTriggerPosition, setMenuTriggerPosition] = useState({ x: 0, y: 0 });

    useEventListener(
        MouseEvents.ContextMenu,
        (event) => {
            event.preventDefault();
            const { pageX, pageY } = event;
            const containerClientRect = (containerRef.current as HTMLElement).getBoundingClientRect();

            menuOverlayState.toggle();
            setMenuTriggerPosition({ x: pageX - containerClientRect.left, y: pageY - containerClientRect.top });
        },
        containerRef
    );

    const handleOnAction = (key: Key): void => {
        menuOverlayState.close();
        const optionKey = String(key).toLocaleLowerCase();
        const [, action] = options.find(([iKey]) => iKey.toLocaleLowerCase() === optionKey) as [string, () => void];

        isFunction(action) && action();
    };

    return (
        <>
            <Button
                variant={'primary'}
                ref={menuTriggerRef}
                aria-label='context menu'
                position={'absolute'}
                top={menuTriggerPosition.y}
                left={menuTriggerPosition.x}
                UNSAFE_style={{ minBlockSize: 0, border: 0, visibility: 'hidden' }}
            ></Button>

            <CustomPopover
                ref={menuTriggerRef}
                state={menuOverlayState}
                placement={'bottom'}
                UNSAFE_style={{ border: 'none' }}
            >
                <Menu onAction={handleOnAction}>
                    {options.map(([item]) => (
                        <Item key={item.toLocaleLowerCase()} aria-label={item.toLocaleLowerCase()}>
                            {item}
                        </Item>
                    ))}
                </Menu>
            </CustomPopover>
        </>
    );
};
