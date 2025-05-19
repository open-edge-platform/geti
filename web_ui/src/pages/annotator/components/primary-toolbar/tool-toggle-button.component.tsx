// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { ReactNode } from 'react';

import { Tooltip, TooltipTrigger } from '@geti/ui';
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
