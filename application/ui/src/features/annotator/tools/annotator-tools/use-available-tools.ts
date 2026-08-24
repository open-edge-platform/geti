// Copyright (C) 2025 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

import { BoundingBox, Polygon, SegmentAnythingIcon, Selector } from '@geti-ui/ui/icons';

import { ReactComponent as MagneticLasso } from '../../../../assets/icons/magnetic-lasso.svg';
import BoundingBoxImg from '../../../../assets/tools/bounding-box.webp';
import MagneticLassoImg from '../../../../assets/tools/magnetic-lasso.webp';
import PolygonImg from '../../../../assets/tools/polygon.webp';
import SAMDetectionImg from '../../../../assets/tools/sam-detection.webp';
import SAMSegmentationImg from '../../../../assets/tools/sam-segmentation.webp';
import { useProjectTask } from '../../../../hooks/use-project-task.hook';
import { HOTKEYS } from '../../../../shared/hotkeys-definition';
import { useSelectedMediaItem } from '../../selected-media-item-provider.component';
import { ToolConfig } from '../interface';
import { canRasteriseAtFullSize } from '../utils';

const SELECTION_TOOL_CONFIG: ToolConfig = {
    type: 'selection',
    icon: Selector,
    hotkey: HOTKEYS.selectionTool,
    labelKey: 'annotator.selectionTool',
    ariaLabelKey: 'annotator.toolSelectionAria',
};

const BOUNDING_BOX_TOOL_CONFIG: ToolConfig = {
    type: 'bounding-box',
    icon: BoundingBox,
    hotkey: HOTKEYS.boundingBoxTool,
    labelKey: 'annotator.boundingBoxTool',
    ariaLabelKey: 'annotator.toolBoundingBoxAria',
    tooltip: {
        img: BoundingBoxImg,
        descriptionKey: 'annotator.tooltipBoundingBox',
    },
};

const AUTO_SEGMENTATION_DETECTION_CONFIG: ToolConfig = {
    type: 'sam',
    icon: SegmentAnythingIcon,
    hotkey: HOTKEYS.autoSegmentation,
    labelKey: 'annotator.autoSegmentationTool',
    ariaLabelKey: 'annotator.toolSamAria',
    tooltip: {
        img: SAMDetectionImg,
        descriptionKey: 'annotator.tooltipSamDetection',
    },
};

const AUTO_SEGMENTATION_CONFIG: ToolConfig = {
    type: 'sam',
    icon: SegmentAnythingIcon,
    hotkey: HOTKEYS.autoSegmentation,
    labelKey: 'annotator.autoSegmentationTool',
    ariaLabelKey: 'annotator.toolSamAria',
    tooltip: {
        img: SAMSegmentationImg,
        descriptionKey: 'annotator.tooltipSamSegmentation',
    },
};

const POLYGON_TOOL_CONFIG: ToolConfig = {
    type: 'polygon',
    icon: Polygon,
    hotkey: HOTKEYS.polygonTool,
    labelKey: 'annotator.polygonTool',
    ariaLabelKey: 'annotator.toolPolygonAria',
    tooltip: {
        img: PolygonImg,
        descriptionKey: 'annotator.tooltipPolygon',
    },
};

const MAGNETIC_LASSO_TOOL_CONFIG: ToolConfig = {
    type: 'magnetic-lasso',
    icon: MagneticLasso,
    hotkey: HOTKEYS.magneticLassoTool,
    labelKey: 'annotator.magneticLassoTool',
    ariaLabelKey: 'annotator.toolMagneticLassoAria',
    tooltip: {
        img: MagneticLassoImg,
        descriptionKey: 'annotator.tooltipMagneticLasso',
    },
};

const TASK_TOOL_CONFIG: Record<string, ToolConfig[]> = {
    classification: [],
    detection: [SELECTION_TOOL_CONFIG, BOUNDING_BOX_TOOL_CONFIG, AUTO_SEGMENTATION_DETECTION_CONFIG],
    instance_segmentation: [
        SELECTION_TOOL_CONFIG,
        POLYGON_TOOL_CONFIG,
        MAGNETIC_LASSO_TOOL_CONFIG,
        AUTO_SEGMENTATION_CONFIG,
    ],
};

export const useAvailableTools = (): ToolConfig[] => {
    const taskType = useProjectTask();
    const { mediaItem } = useSelectedMediaItem();

    // Disable smart tools (SAM, magnetic lasso, SSIM) for oversized media.
    if (!canRasteriseAtFullSize(mediaItem.width, mediaItem.height)) {
        return TASK_TOOL_CONFIG[taskType].filter(
            (tool) => tool.type !== 'sam' && tool.type !== 'magnetic-lasso' && tool.type !== 'ssim'
        );
    }

    return TASK_TOOL_CONFIG[taskType];
};
