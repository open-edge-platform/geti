// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { ComponentProps, ReactNode, RefObject, useEffect, useRef } from 'react';

import { TextField } from '@adobe/react-spectrum';
import { CustomPopover } from '@geti/ui';
import { useUnwrapDOMRef } from '@react-spectrum/utils';
import { OverlayTriggerState, useOverlayTriggerState } from '@react-stately/overlays';
import { TextFieldRef } from '@react-types/textfield';

import { Label } from '../../../../../core/labels/label.interface';
import { BaseLabelSearch } from './base-label-search.component';
import { SearchLabelTreeItemSuffix } from './search-label-tree-view-item.component';

interface PopoverWrapperProps {
    children: ReactNode;
    triggerState: OverlayTriggerState;
    triggerRef: RefObject<TextFieldRef>;
    minWidth: number;
}
const PopoverWrapper = ({ children, triggerState, triggerRef, minWidth }: PopoverWrapperProps) => {
    return (
        <CustomPopover placement='bottom left' state={triggerState} ref={triggerRef} minWidth={minWidth}>
            {children}
        </CustomPopover>
    );
};

interface LabelSearchProps {
    labels: ReadonlyArray<Label>;
    onClick: (label: Label | null) => void;

    // Optional
    id?: string;
    suffix?: SearchLabelTreeItemSuffix;
    prefix?: SearchLabelTreeItemSuffix;
    onClose?: () => void;
    dontFocusOnMount?: boolean;
    textFieldProps?: ComponentProps<typeof TextField>;
}

export const LabelSearch = ({
    id,
    labels,
    onClick,
    onClose,
    suffix,
    prefix,
    dontFocusOnMount = false,
    textFieldProps = {},
}: LabelSearchProps) => {
    const triggerRef = useRef<TextFieldRef>(null);
    const triggerState = useOverlayTriggerState({
        onOpenChange: (isOpen) => {
            if (triggerRef.current && isOpen === false) {
                // Prevents the user from having to "double" click to
                // unfocus this element
                triggerRef.current.getInputElement()?.blur();
                if (onClose) {
                    onClose();
                }
            }
        },
    });

    const onSelectTextField = () => {
        triggerState.open();
    };

    useEffect(() => {
        if (dontFocusOnMount === false) {
            triggerState.open();
        }
        // eslint-disable-next-line react-hooks/exhaustive-deps
    }, [dontFocusOnMount]);

    const unwrapped = useUnwrapDOMRef(triggerRef);
    const minWidth = unwrapped.current?.clientWidth ?? undefined;

    return (
        <BaseLabelSearch
            id={id}
            ref={triggerRef}
            textFieldProps={{
                ...textFieldProps,
                onSelect: onSelectTextField,
                onFocus: onSelectTextField,
            }}
            suffix={suffix}
            prefix={prefix}
            labels={labels}
            onClick={(label) => {
                triggerRef.current?.getInputElement()?.blur();
                triggerState.close();
                onClick(label);
            }}
            dontFocusOnMount={dontFocusOnMount}
            resultWrapperProps={{ triggerState, triggerRef, minWidth }}
            // @ts-expect-error we assume that BaseLabelSearch passes resultWrapperProps to PopoverWrapper
            ResultWrapper={PopoverWrapper}
        />
    );
};
