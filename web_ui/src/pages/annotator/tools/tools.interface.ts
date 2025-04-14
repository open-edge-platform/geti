// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { FunctionComponent, PropsWithChildren, ReactNode } from 'react';

import { Annotation } from '../../../core/annotations/annotation.interface';
import { DOMAIN } from '../../../core/projects/core.interface';
import { AnnotationToolContext, ToolType } from '../core/annotation-tool-context.interface';

export enum PointerEvents {
    PointerDown = 'pointerdown',
    PointerUp = 'pointerup',
    PointerMove = 'pointermove',
    PointerLeave = 'pointerleave',
    ContextMenu = 'contextmenu',
}

export enum PointerType {
    Mouse = 'mouse',
    Pen = 'pen',
    Touch = 'touch',
}

export interface ToolAnnotationContextProps {
    annotationToolContext: AnnotationToolContext;
}

export interface PolygonSelectionToolbarProps {
    polygonAnnotations: Annotation[];
    annotationToolContext: AnnotationToolContext;
}

export interface StateProviderProps {
    children: ReactNode;
}

export interface ToolTooltipProps {
    img: string;
    url: string;
    title: string;
    description: string;
}

export interface ToolProps {
    type: ToolType;
    label: string;
    Icon: FunctionComponent<PropsWithChildren<unknown>>;
    tooltip?: ToolTooltipProps;
    Tool: FunctionComponent<PropsWithChildren<ToolAnnotationContextProps>>;
    SecondaryToolbar: FunctionComponent<PropsWithChildren<ToolAnnotationContextProps>>;
    supportedDomains: DOMAIN[];
    StateProvider: FunctionComponent<PropsWithChildren<StateProviderProps>>;
}
