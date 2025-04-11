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
