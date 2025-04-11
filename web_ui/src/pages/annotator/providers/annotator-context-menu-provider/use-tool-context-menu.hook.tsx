// INTEL CONFIDENTIAL
//
// Copyright (C) 2023 Intel Corporation
//
// This software and the related documents are Intel copyrighted materials, and your use of them is governed by
// the express license under which they were provided to you ("License"). Unless the License provides otherwise,
// you may not use, modify, copy, publish, distribute, disclose or transmit this software or the related documents
// without Intel's prior written permission.
//
// This software and the related documents are provided as is, with no express or implied warranties,
// other than those that are expressly stated in the License.

import { Key, useMemo } from 'react';

import isEmpty from 'lodash/isEmpty';
import { useControls } from 'react-zoom-pan-pinch';

import { FitScreen, Invisible, NoStamp, Redo, Undo, Visible } from '../../../../assets/icons';
import { Point } from '../../../../core/annotations/shapes.interface';
import { isKeypointTask } from '../../../../core/projects/utils';
import { hasEqualId } from '../../../../shared/utils';
import { useDisabledTools } from '../../components/primary-toolbar/utils';
import { AnnotationToolContext, ToolLabel, ToolType } from '../../core/annotation-tool-context.interface';
import { useAnnotatorHotkeys } from '../../hooks/use-hotkeys-configuration.hook';
import {
    useIsSelectionToolActive,
    useSelectingState,
} from '../../tools/selecting-tool/selecting-state-provider.component';
import { SelectingToolType } from '../../tools/selecting-tool/selecting-tool.enums';
import { ToolProps } from '../../tools/tools.interface';
import { useUndoRedo } from '../../tools/undo-redo/undo-redo-provider.component';
import { useAvailableTools } from '../../tools/use-available-tools.hook';
import { toolLabelToTypeMapping, toolTypeToLabelMapping } from '../../tools/utils';
import { usePrediction } from '../prediction-provider/prediction-provider.component';
import { useTaskChainOutput } from '../task-chain-provider/use-task-chain-output.hook';
import { useTask } from '../task-provider/task-provider.component';
import { useAnnotatorContextMenu } from './annotator-context-menu-provider.component';
import { ToolContextMenuItemsKeys } from './utils';

interface UseToolContextMenu {
    annotationToolContext: AnnotationToolContext;
}

const TOOL_CONTEXT_ID = 'Tool context menu';

export const useToolContextMenu = ({ annotationToolContext }: UseToolContextMenu) => {
    const { explanations } = usePrediction();
    const { hotkeys } = useAnnotatorHotkeys();
    const { resetTransform } = useControls();
    const { activeDomains, selectedTask, tasks } = useTask();
    const { undo, redo, canRedo, canUndo } = useUndoRedo();
    const availableTools = useAvailableTools(activeDomains);

    const annotations = useTaskChainOutput(tasks, selectedTask);
    const allAnnotationsHidden = useMemo(() => annotations.every((annotation) => annotation.isHidden), [annotations]);
    const areToolsDisabled = useDisabledTools(annotationToolContext);
    const hasKeypointTasks = tasks.some(isKeypointTask);

    const { showContextMenu } = useAnnotatorContextMenu();

    const { handleCancelStamp } = useSelectingState();
    const isStampToolActive = useIsSelectionToolActive(SelectingToolType.StampTool);
    const {
        toggleTool,
        scene: { setHiddenAnnotations },
    } = annotationToolContext;

    const toggleVisibility = (isHidden: boolean) => {
        setHiddenAnnotations((annotation) => {
            if (annotations.some(hasEqualId(annotation.id))) {
                return isHidden;
            }

            return annotation.isHidden;
        });
    };

    const getToolMenuItems = () => {
        // We have 6 groups of items at the maximum.
        // 1. Cancel stamp.
        // 2. Selection.
        // 3. Basic tools.
        // 4. Smart tools.
        // 5. Undo, redo, explanation.
        // 6. Fit image, hide annotations.
        const selection = availableTools.find(({ type }) => type === ToolType.SelectTool) as ToolProps;
        const basicTools = availableTools.filter(({ type }) =>
            [ToolType.BoxTool, ToolType.CircleTool, ToolType.PolygonTool, ToolType.RotatedBoxTool].includes(type)
        );
        const smartTools = availableTools.filter(({ type }) =>
            [ToolType.GrabcutTool, ToolType.WatershedTool, ToolType.RITMTool, ToolType.SSIMTool].includes(type)
        );

        const explanation = availableTools.find(({ type }) => type === ToolType.Explanation);

        const fitHideGroup = [
            { title: ToolContextMenuItemsKeys.FIT_IMAGE, icon: <FitScreen />, shortcut: hotkeys.zoom },
            {
                title: allAnnotationsHidden
                    ? ToolContextMenuItemsKeys.SHOW_ANNOTATIONS
                    : ToolContextMenuItemsKeys.HIDE_ANNOTATIONS,
                icon: allAnnotationsHidden ? <Invisible /> : <Visible />,
                shortcut: hotkeys.hideAllAnnotations,
            },
        ];

        const explanationFitHideGroup = explanation
            ? [
                  { title: explanation.label, icon: <explanation.Icon />, shortcut: hotkeys['explanation'] },
                  ...fitHideGroup,
              ]
            : fitHideGroup;

        const tools = [
            {
                id: `${selection.label} tool`,
                children: [{ title: selection.label, icon: <selection.Icon />, shortcut: hotkeys['select-tool'] }],
            },
            {
                id: 'Basic tools',
                children: basicTools.map((tool) => ({
                    title: tool.label,
                    icon: <tool.Icon />,
                    shortcut: hotkeys[tool.type],
                })),
            },
            {
                id: 'Smart tools',
                children: smartTools.map((tool) => ({
                    title: tool.label,
                    icon: <tool.Icon />,
                    shortcut: hotkeys[tool.type],
                })),
            },
            {
                id: 'Undo, redo',
                children: [
                    { title: ToolContextMenuItemsKeys.UNDO, icon: <Undo />, shortcut: hotkeys.undo },
                    { title: ToolContextMenuItemsKeys.REDO, icon: <Redo />, shortcut: hotkeys.redo },
                ],
            },
            {
                id: explanation ? `Explanation, fit image, hide annotations` : 'Fit image, hide annotations',
                children: explanationFitHideGroup,
            },
        ];

        return isStampToolActive
            ? [
                  {
                      id: `${ToolContextMenuItemsKeys.CANCEL_STAMP} tool`,
                      children: [
                          {
                              title: ToolContextMenuItemsKeys.CANCEL_STAMP,
                              icon: <NoStamp />,
                              shortcut: hotkeys.close.slice(0, 3),
                          },
                      ],
                  },
                  ...tools,
              ]
            : tools;
    };

    const handleToolContextMenuAction = (key: Key): void => {
        switch (key) {
            case ToolContextMenuItemsKeys.CANCEL_STAMP: {
                handleCancelStamp();

                break;
            }
            case ToolContextMenuItemsKeys.UNDO: {
                undo();

                break;
            }
            case ToolContextMenuItemsKeys.REDO: {
                redo();

                break;
            }
            case ToolContextMenuItemsKeys.FIT_IMAGE: {
                resetTransform();

                break;
            }
            case ToolContextMenuItemsKeys.SHOW_ANNOTATIONS:
            case ToolContextMenuItemsKeys.HIDE_ANNOTATIONS: {
                toggleVisibility(!allAnnotationsHidden);
                break;
            }
            case ToolLabel.SelectTool: {
                isStampToolActive ? handleCancelStamp() : toggleTool(toolLabelToTypeMapping[key]);

                break;
            }
            case ToolLabel.BoxTool:
            case ToolLabel.PolygonTool:
            case ToolLabel.RotatedBoxTool:
            case ToolLabel.RITMTool:
            case ToolLabel.WatershedTool:
            case ToolLabel.SSIMTool:
            case ToolLabel.GrabcutTool:
            case ToolLabel.CircleTool:
            case ToolLabel.Explanation: {
                toggleTool(toolLabelToTypeMapping[key]);

                break;
            }
        }
    };

    const handleShowToolContextMenu = ({ x, y }: Point): void => {
        const disabledKeys: string[] = [];
        if (!canUndo) {
            disabledKeys.push(ToolContextMenuItemsKeys.UNDO);
        }

        if (!canRedo) {
            disabledKeys.push(ToolContextMenuItemsKeys.REDO);
        }

        if (isEmpty(explanations)) {
            disabledKeys.push(toolTypeToLabelMapping[ToolType.Explanation]);
        }

        if (hasKeypointTasks) {
            disabledKeys.push(ToolContextMenuItemsKeys.HIDE_ANNOTATIONS);
            disabledKeys.push(ToolContextMenuItemsKeys.SHOW_ANNOTATIONS);
        }

        if (areToolsDisabled) {
            disabledKeys.push(toolTypeToLabelMapping[ToolType.BoxTool]);
            disabledKeys.push(toolTypeToLabelMapping[ToolType.RotatedBoxTool]);
            disabledKeys.push(toolTypeToLabelMapping[ToolType.CircleTool]);
            disabledKeys.push(toolTypeToLabelMapping[ToolType.PolygonTool]);
            disabledKeys.push(toolTypeToLabelMapping[ToolType.RITMTool]);
            disabledKeys.push(toolTypeToLabelMapping[ToolType.WatershedTool]);
            disabledKeys.push(toolTypeToLabelMapping[ToolType.GrabcutTool]);
            disabledKeys.push(toolTypeToLabelMapping[ToolType.SSIMTool]);
        }

        showContextMenu({
            contextId: TOOL_CONTEXT_ID,
            handleMenuAction: handleToolContextMenuAction,
            menuPosition: {
                top: y,
                left: x,
            },
            menuItems: getToolMenuItems(),
            ariaLabel: TOOL_CONTEXT_ID,
            disabledKeys,
        });
    };

    return {
        handleShowToolContextMenu,
    };
};
