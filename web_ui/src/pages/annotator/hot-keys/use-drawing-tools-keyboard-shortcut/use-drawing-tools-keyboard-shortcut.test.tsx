// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { ReactNode } from 'react';

import { fireEvent, renderHook, waitFor } from '@testing-library/react';

import { getMockedDatasetIdentifier } from '../../../../test-utils/mocked-items-factory/mocked-identifiers';
import { RequiredProviders } from '../../../../test-utils/required-providers-render';
import { ToolType } from '../../core/annotation-tool-context.interface';
import { AnnotatorProviders } from '../../test-utils/annotator-render';
import { GrabcutToolType } from '../../tools/grabcut-tool/grabcut-tool.enums';
import { PolygonMode } from '../../tools/polygon-tool/polygon-tool.enum';
import { useDrawingToolsKeyboardShortcut } from './use-drawing-tools-keyboard-shortcut';

jest.mock('react-router-dom', () => ({
    ...jest.requireActual('react-router-dom'),
    useLocation: jest.fn(),
}));

const wrapper = ({ children }: { children: ReactNode }) => {
    const datasetIdentifier = getMockedDatasetIdentifier();

    return (
        <RequiredProviders>
            <AnnotatorProviders datasetIdentifier={datasetIdentifier}>{children}</AnnotatorProviders>
        </RequiredProviders>
    );
};

describe('useDrawingToolsKeyboardShortcut', () => {
    // Get all tools with their hotkeys and keycodes, excluding EditTool (which has no shortcut key assigned)
    const tools = [
        [ToolType.SelectTool, 'v', 86],
        [ToolType.BoxTool, 'b', 66],
        [ToolType.CircleTool, 'c', 67],
        [ToolType.PolygonTool, 'p', 80],
        [ToolType.GrabcutTool, 'g', 71],
        [ToolType.WatershedTool, 'w', 87],
    ];

    it.each(tools)('should execute the callback for %p hotkey', async (tool, hotkey, keyCode) => {
        const mockOnSelect = jest.fn();

        renderHook(
            () =>
                useDrawingToolsKeyboardShortcut(
                    tool as ToolType | GrabcutToolType | PolygonMode.MagneticLasso,
                    mockOnSelect
                ),
            {
                wrapper,
            }
        );

        await waitFor(() => {
            fireEvent.keyDown(document.body, { key: hotkey, keyCode });

            expect(mockOnSelect).toHaveBeenCalledTimes(1);
        });
    });
});
