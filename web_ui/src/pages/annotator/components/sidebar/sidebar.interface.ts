// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { Dispatch, SetStateAction } from 'react';

import { ViewModes } from '@shared/components/media-view-modes/utils';

import { AnnotationToolContext } from '../../core/annotation-tool-context.interface';

export interface SidebarCommonProps {
    showDatasetPanel: boolean;
    showCountingPanel: boolean;
    showAnnotationPanel: boolean;
    annotationToolContext: AnnotationToolContext;
    datasetViewMode: ViewModes;
    setDatasetViewMode: Dispatch<SetStateAction<ViewModes>>;
}
