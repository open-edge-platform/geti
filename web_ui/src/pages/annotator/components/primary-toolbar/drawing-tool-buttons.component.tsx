// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { ReactNode } from 'react';

import { Tooltip, TooltipTrigger } from '@adobe/react-spectrum';
import { Flex } from '@react-spectrum/layout';

import { QuietToggleButton } from '../../../../shared/components/quiet-button/quiet-toggle-button.component';
import { ToolType } from '../../core/annotation-tool-context.interface';
import { useAnnotatorHotkeys } from '../../hooks/use-hotkeys-configuration.hook';
import { useDrawingToolsKeyboardShortcut } from '../../hot-keys/use-drawing-tools-keyboard-shortcut/use-drawing-tools-keyboard-shortcut';
import { ToolProps } from '../../tools/tools.interface';
import { DrawingToolsTooltip } from './drawing-tools-tooltip.component';
import { PrimaryToolbarButtonProps } from './primary-toolbar-button.interface';

import classes from './primaryToolBar.module.scss';

interface DrawingToolButtonsProps extends PrimaryToolbarButtonProps {
    id?: string;
    drawingTools: ToolProps[];
    isDisabled: boolean;
}

const DrawingToggleButtonShortcut = ({
    type,
    children,
    onSelect,
}: {
    children: ReactNode;
    type: ToolType;
    onSelect: () => void;
}): JSX.Element => {
    useDrawingToolsKeyboardShortcut(type, onSelect);

    return <> {children} </>;
};

export const DrawingToolButtons = ({
    id,
    drawingTools,
    activeTool,
    setActiveTool,
    isDisabled,
}: DrawingToolButtonsProps): JSX.Element => {
    const { hotkeys } = useAnnotatorHotkeys();

    return (
        <Flex
            direction='column'
            gap='size-100'
            alignItems='center'
            justify-content='center'
            data-testid={`${id}-drawing-tools-container`}
        >
            {drawingTools.map((tool, index) => {
                const { tooltip } = tool;
                const onSelect = () => setActiveTool(tool.type);

                return (
                    <DrawingToggleButtonShortcut type={tool.type} onSelect={onSelect} key={`tooltip-${tool}-${index}`}>
                        <TooltipTrigger placement={tooltip ? 'bottom' : 'right top'}>
                            <QuietToggleButton
                                onPress={onSelect}
                                aria-label={tool.label}
                                id={tool.type.toString()}
                                isDisabled={isDisabled}
                                isSelected={tool.type === activeTool}
                            >
                                {<tool.Icon />}
                            </QuietToggleButton>
                            <Tooltip UNSAFE_className={tooltip ? classes.drawingToolsTooltips : ''}>
                                {tooltip ? (
                                    <DrawingToolsTooltip {...tooltip} hotkey={hotkeys[tool.type]} />
                                ) : (
                                    tool.label
                                )}
                            </Tooltip>
                        </TooltipTrigger>
                    </DrawingToggleButtonShortcut>
                );
            })}
        </Flex>
    );
};
