// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { DOMAIN } from '../../../core/projects/core.interface';
import { BoundingBoxTool } from './bounding-box';
import { CircleTool } from './circle-tool';
import { ExplanationTool } from './explanation-tool';
import { GrabcutTool } from './grabcut-tool';
import { KeypointTool } from './keypoint-tool';
import { PolygonTool } from './polygon-tool';
import { RITMTool } from './ritm-tool';
import { RotatedBoundingBoxTool } from './rotated-bounding-box-tool';
import { SegmentAnythingTool } from './segment-anything-tool';
import { SelectingTool } from './selecting-tool';
import { SSIMTool } from './ssim-tool';
import { ToolProps } from './tools.interface';
import { WatershedTool } from './watershed-tool';

const ALL_TOOLS: ToolProps[] = [
    SelectingTool,
    PolygonTool,
    RotatedBoundingBoxTool,
    BoundingBoxTool,
    CircleTool,
    SegmentAnythingTool,
    RITMTool,
    GrabcutTool,
    WatershedTool,
    SSIMTool,
    ExplanationTool,
    KeypointTool,
];

export const useAvailableTools = (activeDomains: DOMAIN[]): ToolProps[] => {
    return ALL_TOOLS.filter(({ supportedDomains }) => {
        return activeDomains.some((domain: DOMAIN) => {
            return supportedDomains.includes(domain);
        });
    });
};
