// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { useMemo, useState } from 'react';

import { Annotation } from '../../../../core/annotations/annotation.interface';
import { AnnotationScene } from '../../core/annotation-scene.interface';
import { ToolType } from '../../core/annotation-tool-context.interface';
import { ExtendedToolType, toolTypeToLabelMapping } from '../../tools/utils';

export type ToolPerAnnotation = Record<string, string>;

export interface ToolPerAnnotationState {
    toolPerAnnotation: ToolPerAnnotation;
    resetToolPerAnnotation: () => void;
}

type EnhancedAnalyticsAnnotationScene = [AnnotationScene, ToolPerAnnotationState];

const assignToolsPerAnnotations = (
    toolPerAnnotation: ToolPerAnnotation,
    annotations: Annotation[],
    activeTool: ExtendedToolType
): ToolPerAnnotation => {
    const newToolsPerAnnotations = { ...toolPerAnnotation };

    annotations.forEach(({ id }) => {
        newToolsPerAnnotations[id] = toolTypeToLabelMapping[activeTool];
    });

    return newToolsPerAnnotations;
};

const initialState: ToolPerAnnotation = {};

export const useEnhancedAnalyticsAnnotationScene = (
    parentScene: AnnotationScene,
    activeTool: ToolType
): EnhancedAnalyticsAnnotationScene => {
    const [toolPerAnnotation, setToolPerAnnotation] = useState<ToolPerAnnotation>(initialState);

    const resetToolPerAnnotation = () => {
        setToolPerAnnotation(initialState);
    };

    const scene = useMemo<AnnotationScene>(() => {
        const addShapes: AnnotationScene['addShapes'] = (...args) => {
            const annotations = parentScene.addShapes(...args);

            const newToolPerAnnotation = assignToolsPerAnnotations(toolPerAnnotation, annotations, activeTool);

            setToolPerAnnotation(newToolPerAnnotation);

            return annotations;
        };

        const addAnnotations: AnnotationScene['addAnnotations'] = (annotations) => {
            const newToolPerAnnotation = assignToolsPerAnnotations(toolPerAnnotation, annotations, activeTool);

            setToolPerAnnotation(newToolPerAnnotation);

            parentScene.addAnnotations(annotations);
        };

        const removeAnnotations: AnnotationScene['removeAnnotations'] = (annotations, skipHistory) => {
            const newToolsPerAnnotations = { ...toolPerAnnotation };

            annotations.forEach(({ id }) => {
                delete newToolsPerAnnotations[id];
            });

            setToolPerAnnotation(newToolsPerAnnotations);

            parentScene.removeAnnotations(annotations, skipHistory);
        };

        return {
            ...parentScene,

            addShapes,
            addAnnotations,
            removeAnnotations,
        };
    }, [parentScene, activeTool, toolPerAnnotation]);

    return [scene, { toolPerAnnotation, resetToolPerAnnotation }];
};
