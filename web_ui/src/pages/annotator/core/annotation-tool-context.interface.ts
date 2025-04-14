// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { Annotation } from '../../../core/annotations/annotation.interface';
import { ShapeType } from '../../../core/annotations/shapetype.enum';
import { Label } from '../../../core/labels/label.interface';
import { DOMAIN } from '../../../core/projects/core.interface';
import { Task } from '../../../core/projects/task.interface';
import { GrabcutToolType } from '../tools/grabcut-tool/grabcut-tool.enums';
import { PolygonMode } from '../tools/polygon-tool/polygon-tool.enum';
import { SelectingToolType } from '../tools/selecting-tool/selecting-tool.enums';
import { WatershedLabel } from '../tools/watershed-tool/watershed-tool.interface';
import { AnnotationScene } from './annotation-scene.interface';

export enum ToolType {
    SelectTool = 'select-tool',
    SSIMTool = 'ssim-tool',
    RITMTool = 'ritm-tool',
    SegmentAnythingTool = 'segment-anything-tool',
    EditTool = 'edit-tool',
    BoxTool = 'bounding-box-tool',
    RotatedBoxTool = 'rotated-bounding-box-tool',
    CircleTool = 'circle-tool',
    PolygonTool = 'polygon-tool',
    GrabcutTool = 'grabcut-tool',
    WatershedTool = 'watershed-tool',
    Explanation = 'explanation',
    KeypointTool = 'keypoint-tool',
}

export enum ToolLabel {
    SelectTool = 'Selection',
    SSIMTool = 'Detection assistant',
    RITMTool = 'Interactive segmentation',
    SegmentAnythingTool = 'Auto segmentation',
    BoxTool = 'Bounding Box',
    RotatedBoxTool = 'Rotated Bounding Box',
    CircleTool = 'Circle',
    PolygonTool = 'Polygon',
    GrabcutTool = 'Quick Selection',
    EditTool = 'Edit',
    WatershedTool = 'Object coloring',
    Explanation = 'Explanation',
    KeypointTool = 'Keypoint tool',
}

export enum ANNOTATOR_MODE {
    PREDICTION = 'predictions',
    ACTIVE_LEARNING = 'active-learning',
}

export interface ToolSettings {
    [ToolType.CircleTool]: {
        size: number;
    };
    [ToolType.WatershedTool]: {
        brushSize: number;
        label?: WatershedLabel;
        sensitivity: number;
    };
    [ToolType.RITMTool]: {
        selectedLabel?: Label;
        dynamicBoxMode: boolean;
        rightClickMode: boolean;
    };
    [ToolType.SegmentAnythingTool]: {
        selectedLabel?: Label;
        maskOpacity: number;
        interactiveMode: boolean;
        rightClickMode: boolean;
    };
    [ToolType.SelectTool]: {
        tool: SelectingToolType;
        brushSize: number | null;
        stampedAnnotation: Annotation | null;
    };
    [ToolType.GrabcutTool]: {
        selectedLabel?: Label;
        sensitivity: number;
    };
    [ToolType.SSIMTool]: {
        autoMergeDuplicates: boolean;
        shapeType: ShapeType;
        selectedLabel?: Label;
    };
    [ToolType.PolygonTool]: {
        mode: PolygonMode | null;
    };
}

export type ToolSpecificSettings<T extends keyof ToolSettings> = Pick<ToolSettings, T>[T];
export type UpdateToolSettings<T extends keyof ToolSettings> = Partial<ToolSpecificSettings<T>>;

export type TaskMode = DOMAIN | 'All';

export type ToolsSettings = Map<keyof ToolSettings, ToolSettings[keyof ToolSettings]>;

export type ToolsSettingsPerTask = Record<TaskMode, ToolsSettings>;

export interface AnnotationToolContext {
    readonly scene: AnnotationScene;
    readonly tool: ToolType;
    readonly toolsSettings: ToolsSettingsPerTask;

    toggleTool: (tool: ToolType, updateLastTool?: boolean) => void;
    toggleToolOnTaskChange: (newSelectedTask: Task | null) => void;
    getToolSettings: <T extends keyof ToolSettings>(type: T) => ToolSpecificSettings<T>;
    updateToolSettings: <T extends keyof ToolSettings>(type: T, settings: UpdateToolSettings<T>) => void;
}

export type DefaultToolTypes = ToolType | GrabcutToolType | SelectingToolType | PolygonMode.MagneticLasso;
