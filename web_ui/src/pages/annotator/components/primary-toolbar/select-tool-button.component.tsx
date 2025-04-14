// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { Selector } from '../../../../assets/icons';
import { ToolLabel, ToolType } from '../../core/annotation-tool-context.interface';
import { PrimaryToolbarButtonProps } from './primary-toolbar-button.interface';
import { ToolToggleButton } from './tool-toggle-button.component';

export const SelectToolButton = ({ activeTool, setActiveTool }: PrimaryToolbarButtonProps): JSX.Element => {
    const handleSetActiveTool = () => {
        setActiveTool(ToolType.SelectTool);
    };

    return (
        <ToolToggleButton
            type={ToolType.SelectTool}
            label={ToolLabel.SelectTool}
            isActive={activeTool === ToolType.SelectTool}
            onSelect={handleSetActiveTool}
        >
            <Selector />
        </ToolToggleButton>
    );
};
