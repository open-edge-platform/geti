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

import { ComponentProps, forwardRef, ReactNode, RefObject, useRef } from 'react';

import { Popover } from '@react-spectrum/overlays';
import { useUnwrapDOMRef } from '@react-spectrum/utils';
import { OverlayTriggerState } from '@react-stately/overlays';
import { OverlayProps } from '@react-types/overlays';
import { DOMRefValue } from '@react-types/shared';
import { DismissButton, FocusScope, useOverlay } from 'react-aria';

interface CustomPopoverProps
    extends Omit<ComponentProps<typeof Popover>, 'triggerRef'>,
        Omit<OverlayProps, 'nodeRef' | 'container'> {
    children: ReactNode;
    hideArrow?: boolean;
    state: OverlayTriggerState;
    width?: number;
}

export const CustomPopover = forwardRef<DOMRefValue, CustomPopoverProps>(
    ({ state: popoverState, children, width, placement, hideArrow = true, ...rest }, ref) => {
        const triggerRef = ref as RefObject<DOMRefValue>;
        const popoverRef = useRef<DOMRefValue<HTMLDivElement>>(null);
        const unwrappedPopoverRef = useUnwrapDOMRef(popoverRef);
        const unwrappedTriggerRef = useUnwrapDOMRef(triggerRef);

        const { overlayProps } = useOverlay(
            {
                isDismissable: true,
                shouldCloseOnBlur: false,
                isOpen: popoverState.isOpen,
                onClose: popoverState.close,
            },
            unwrappedPopoverRef
        );

        return (
            <FocusScope restoreFocus>
                <Popover
                    isNonModal
                    ref={popoverRef}
                    placement={placement}
                    hideArrow={hideArrow}
                    state={popoverState}
                    triggerRef={unwrappedTriggerRef}
                    UNSAFE_style={{
                        width: width ?? 'unset',
                        minWidth: width ?? 'unset',
                    }}
                    {...rest}
                    {...overlayProps}
                >
                    <>
                        {children}
                        <DismissButton onDismiss={popoverState.close} />
                    </>
                </Popover>
            </FocusScope>
        );
    }
);
