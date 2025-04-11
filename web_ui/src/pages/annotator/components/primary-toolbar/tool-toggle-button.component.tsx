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

import { ReactNode } from 'react';

import { Tooltip, TooltipTrigger } from '@adobe/react-spectrum';
import { Placement } from 'react-aria';

import { QuietToggleButton } from '../../../../shared/components/quiet-button/quiet-toggle-button.component';
import { ToolType } from '../../core/annotation-tool-context.interface';
import { useDrawingToolsKeyboardShortcut } from '../../hot-keys/use-drawing-tools-keyboard-shortcut/use-drawing-tools-keyboard-shortcut';
import { GrabcutToolType } from '../../tools/grabcut-tool/grabcut-tool.enums';
import { SelectingToolType } from '../../tools/selecting-tool/selecting-tool.enums';

interface ToolButtonProps {
    onSelect: () => void;
    label: string;
    isActive: boolean;
    isDisabled?: boolean;
    placement?: Placement;
    children: ReactNode;
    type: ToolType | GrabcutToolType | SelectingToolType;
}

export const ToolToggleButton = ({
    onSelect,
    label,
    isActive,
    type,
    placement = 'right',
    isDisabled = false,
    children,
}: ToolButtonProps): JSX.Element => {
    useDrawingToolsKeyboardShortcut(type, onSelect, isDisabled);

    return (
        <TooltipTrigger placement={placement}>
            <QuietToggleButton
                isDisabled={isDisabled}
                isSelected={isActive}
                onPress={onSelect}
                aria-label={label}
                id={type.toString()}
            >
                {children}
            </QuietToggleButton>
            <Tooltip>{label}</Tooltip>
        </TooltipTrigger>
    );
};
