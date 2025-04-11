// INTEL CONFIDENTIAL
//
// Copyright (C) 2024 Intel Corporation
//
// This software and the related documents are Intel copyrighted materials, and your use of them is governed by
// the express license under which they were provided to you ("License"). Unless the License provides otherwise,
// you may not use, modify, copy, publish, distribute, disclose or transmit this software or the related documents
// without Intel's prior written permission.
//
// This software and the related documents are provided as is, with no express or implied warranties,
// other than those that are expressly stated in the License.

import { Key, RefObject, useRef, useState } from 'react';

import { Item, Menu } from '@adobe/react-spectrum';
import { useOverlayTriggerState } from '@react-stately/overlays';
import isFunction from 'lodash/isFunction';

import { useEventListener } from '../../../../hooks/event-listener/event-listener.hook';
import { Button } from '../../../../shared/components/button/button.component';
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
