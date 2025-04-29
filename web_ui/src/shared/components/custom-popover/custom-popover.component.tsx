// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { ComponentProps, forwardRef, ReactNode, RefObject, useRef } from 'react';

import { Popover } from '@react-spectrum/overlays';
import { useUnwrapDOMRef } from '@react-spectrum/utils';
import { OverlayTriggerState } from '@react-stately/overlays';
import { OverlayProps } from '@react-types/overlays';
import { DOMRefValue } from '@react-types/shared';
import { DismissButton, FocusScope, useInteractOutside, useOverlay } from 'react-aria';

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

        useInteractOutside({
            ref: unwrappedTriggerRef,
            onInteractOutside: (event) => {
                const target = event.target as Element;
                if (unwrappedPopoverRef.current?.contains(target)) {
                    return;
                }

                popoverState.close();
            },
        });

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
