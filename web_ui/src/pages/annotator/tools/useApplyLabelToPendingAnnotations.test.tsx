// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { DOMAIN } from '../../../core/projects/core.interface';
import { fakeAnnotationToolContext } from '../../../test-utils/fake-annotator-context';
import { getMockedLabel } from '../../../test-utils/mocked-items-factory/mocked-labels';
import { renderHookWithProviders } from '../../../test-utils/render-hook-with-providers';
import { ToolSettings, ToolType } from '../core/annotation-tool-context.interface';
import { DEFAULT_TOOLS_SETTINGS } from '../providers/annotation-tool-provider/tools-settings';
import { useApplyLabelToPendingAnnotations } from './useApplyLabelToPendingAnnotations';

const tools: (ToolType.GrabcutTool | ToolType.SSIMTool | ToolType.RITMTool)[] = [
    ToolType.GrabcutTool,
    ToolType.SSIMTool,
    ToolType.RITMTool,
];

describe('useApplyLabelToPendingAnnotations', () => {
    describe('executes the callback once the selected label changes', () => {
        const mockCallback = jest.fn();
        const mockLabel = getMockedLabel({ name: 'random label' });

        it.each(tools)('when using %p tool', async (currentTool) => {
            const context = fakeAnnotationToolContext({
                tool: currentTool,
                toolsSettings: {
                    [DOMAIN.SEGMENTATION]: DEFAULT_TOOLS_SETTINGS,
                },
            });

            context.getToolSettings = jest
                .fn()
                .mockImplementation((tool: keyof ToolSettings) => DEFAULT_TOOLS_SETTINGS.get(tool));

            context.updateToolSettings = (tool, settings) => {
                // @ts-expect-error We dont want to mock all possible settings
                context.toolsSettings.Segmentation.set(tool, settings);
            };

            renderHookWithProviders(() =>
                useApplyLabelToPendingAnnotations({
                    applyAnnotations: mockCallback,
                    annotationToolContext: context,
                    tool: currentTool,
                })
            );

            expect(context.getToolSettings(currentTool).selectedLabel).toBeUndefined();

            context.updateToolSettings(currentTool, {
                selectedLabel: mockLabel,
            });

            expect(context.getToolSettings(currentTool).selectedLabel).toEqual(mockLabel);
        });
    });
});
