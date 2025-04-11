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

import { ReactNode, RefObject, useState } from 'react';

import { View } from '@adobe/react-spectrum';
import { DOMRefValue } from '@react-types/shared';
import { OverlayContainer } from 'react-aria';

import { useEventListener } from '../../../hooks/event-listener/event-listener.hook';
import { MouseEvents } from '../../../shared/mouse-events';
import { ThemeProvider } from '../../../theme/theme-provider.component';

export interface CursorContextMenuProps {
    isOpen: boolean;
    children: ReactNode;
    onOpen: () => void;
    isValidTrigger: (element: Element) => boolean;
    triggerRef: RefObject<Element>;
    containerRef?: RefObject<DOMRefValue<HTMLElement>>;
}

export const X_PADDING = 10;
export const CursorContextMenu = ({
    isOpen,
    children,
    containerRef,
    triggerRef,
    onOpen,
    isValidTrigger,
}: CursorContextMenuProps) => {
    const [cursorPosition, setCursorPosition] = useState({ x: 0, y: 0 });

    useEventListener(
        MouseEvents.ContextMenu,
        (event) => {
            event.preventDefault();

            if (isValidTrigger(event.target as Element)) {
                onOpen();
                setCursorPosition({ x: event.clientX, y: event.clientY });
            }
        },
        triggerRef
    );

    return (
        <OverlayContainer>
            {isOpen && (
                <ThemeProvider>
                    <View
                        ref={containerRef}
                        position={'absolute'}
                        top={cursorPosition.y}
                        left={cursorPosition.x + X_PADDING}
                        zIndex={100001}
                        backgroundColor={'gray-200'}
                        data-testid='position container'
                    >
                        {children}
                    </View>
                </ThemeProvider>
            )}
        </OverlayContainer>
    );
};
