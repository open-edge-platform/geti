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

import { MutableRefObject } from 'react';

import { Annotation, RegionOfInterest } from '../core/annotations/annotation.interface';
import { Label } from '../core/labels/label.interface';
import { DOMAIN } from '../core/projects/core.interface';
import { Task } from '../core/projects/task.interface';
import { AnnotationScene } from '../pages/annotator/core/annotation-scene.interface';
import {
    AnnotationToolContext,
    ANNOTATOR_MODE,
    ToolType,
} from '../pages/annotator/core/annotation-tool-context.interface';
import { DEFAULT_TOOLS_SETTINGS } from '../pages/annotator/providers/annotation-tool-provider/tools-settings';
import { getMockedTask } from './mocked-items-factory/mocked-tasks';

interface Props {
    labels?: Label[];
    annotations?: Annotation[];
    defaultLabel?: Label | null;
    zoom?: number;
    roi?: RegionOfInterest;
    tool?: ToolType;
    toggleTool?: (toolType: ToolType) => void;
    defaultRadius?: number;
    setDefaultRadius?: (radius: number) => void;
    activeDomains?: DOMAIN[];
    mode?: ANNOTATOR_MODE;
    tasks?: Task[];
    selectedTask?: Task | null;
    hasShapePointSelected?: MutableRefObject<boolean>;
    toolsSettings?: Partial<AnnotationToolContext['getToolSettings']>;
    getToolSettings?: AnnotationToolContext['getToolSettings'];
    updateToolSettings?: AnnotationToolContext['updateToolSettings'];
    addLabel?: (
        label: Label,
        annotationIds: string[],
        conflictResolver?: (label: Label, otherLabel: Label) => boolean
    ) => void;
    removeLabels?: (labels: Label[], annotationIds: string[], skipHistory?: boolean) => void;
    isDrawing?: boolean;
    removeAnnotations?: AnnotationScene['removeAnnotations'];
}

export function fakeAnnotationToolContext({
    labels: customLabels = [],
    annotations = [],
    zoom: _,
    toggleTool,
    tool = ToolType.BoxTool,
    tasks = customLabels.length > 0 ? [getMockedTask({ labels: customLabels })] : [],
    isDrawing = false,
    hasShapePointSelected = { current: false },
    getToolSettings = jest.fn(),
    updateToolSettings = jest.fn(),
    toolsSettings = {
        [DOMAIN.DETECTION]: DEFAULT_TOOLS_SETTINGS,
    },
    addLabel = jest.fn(),
    removeLabels = jest.fn(),
    removeAnnotations = jest.fn(),
}: Props = {}): AnnotationToolContext {
    const labels = tasks.length > 0 ? tasks?.flatMap((task) => task.labels) : customLabels;

    return {
        scene: {
            labels,
            annotations,
            isDrawing,
            setIsDrawing: jest.fn(),
            hasShapePointSelected,
            addShapes: jest.fn(),
            allAnnotationsHidden: false,
            addLabel,
            removeLabels,
            addAnnotations: jest.fn(),
            updateAnnotation: jest.fn(),
            removeAnnotations,
            replaceAnnotations: jest.fn(),
            hoverAnnotation: jest.fn(),
            setSelectedAnnotations: jest.fn(),
            setLockedAnnotations: jest.fn(),
            setHiddenAnnotations: jest.fn(),
            selectAnnotation: jest.fn(),
            unselectAllAnnotations: jest.fn(),
            unselectAnnotation: jest.fn(),
            hideAnnotation: jest.fn(),
            toggleLock: jest.fn(),
            showAnnotation: jest.fn(),
        },
        tool,
        getToolSettings,
        updateToolSettings,
        toggleTool: toggleTool ?? jest.fn(),
        toggleToolOnTaskChange: jest.fn(),
        // @ts-expect-error We don't care about all domains
        toolsSettings,
    };
}
