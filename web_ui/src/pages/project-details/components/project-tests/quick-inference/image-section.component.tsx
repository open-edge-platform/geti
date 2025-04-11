// INTEL CONFIDENTIAL
//
// Copyright (C) 2022 Intel Corporation
//
// This software and the related documents are Intel copyrighted materials, and your use of them is governed by
// the express license under which they were provided to you ("License"). Unless the License provides otherwise,
// you may not use, modify, copy, publish, distribute, disclose or transmit this software or the related documents
// without Intel's prior written permission.
//
// This software and the related documents are provided as is, with no express or implied warranties,
// other than those that are expressly stated in the License.

import { CSSProperties } from 'react';

import { View } from '@adobe/react-spectrum';
import identity from 'lodash/identity';

import { Layers } from '../../../../annotator/annotation/layers/layers.component';
import { AnnotatorCanvasSettings } from '../../../../annotator/annotator-settings.component';
import { ExplanationMap } from '../../../../annotator/components/explanation/explanation.component';
import { MediaImage } from '../../../../annotator/media-image.component';
import {
    AnnotationToolProvider,
    useAnnotationToolContext,
} from '../../../../annotator/providers/annotation-tool-provider/annotation-tool-provider.component';
import { useAnnotatorCanvasSettings } from '../../../../annotator/providers/annotator-canvas-settings-provider/annotator-canvas-settings-provider.component';
import { useSelectedMediaItem } from '../../../../annotator/providers/selected-media-item-provider/selected-media-item-provider.component';
import { filterForExplanation } from '../../../../annotator/utils';
import { SyncZoomState, SyncZoomTarget } from '../../../../annotator/zoom/sync-zoom-state.component';
import { TransformZoomAnnotation } from '../../../../annotator/zoom/transform-zoom-annotation.component';
import { useZoom, ZoomProvider } from '../../../../annotator/zoom/zoom-provider.component';
import { useQuickInference } from './quick-inference-provider.component';

import classes from './quick-inference.module.scss';

const RawCanvas = () => {
    const annotationToolContext = useAnnotationToolContext();
    const { zoomState } = useZoom();

    const { selectedMediaItem } = useSelectedMediaItem();

    const { canvasSettingsState } = useAnnotatorCanvasSettings();
    const [canvasSettings] = canvasSettingsState;

    const { explanation, showExplanation, explanationOpacity } = useQuickInference();
    const explanationVisible = showExplanation;

    // The QuickInference component only renders ImageSection if the user
    // has selected a media item, so this edge case is not possible.
    if (selectedMediaItem === undefined) {
        return <></>;
    }

    const image = selectedMediaItem.image;

    const annotations = selectedMediaItem.annotations.filter(filterForExplanation(explanation, explanationVisible));

    return (
        <View UNSAFE_style={{ '--zoom-level': zoomState.zoom } as CSSProperties}>
            <div className={classes.canvas}>
                <MediaImage image={image} selectedMediaItem={selectedMediaItem} />

                <ExplanationMap explanation={explanation} opacity={explanationOpacity} enabled={explanationVisible} />

                <Layers
                    width={image.width}
                    height={image.height}
                    showLabelOptions={false}
                    annotations={annotations}
                    annotationsFilter={identity}
                    annotationToolContext={annotationToolContext}
                    hideLabels={Boolean(canvasSettings.hideLabels.value)}
                />
            </div>
        </View>
    );
};

export const ImageSection = (): JSX.Element => {
    // NOTE: the ImageSection renders the ZoomProvider and AnnotationToolProvider so that
    // it will work both when rendered in the Accordion and in the FullScreenAction.
    // If we had moved these providers into the `PreRequiredAnnotatorProviders`, then
    // syncing the zoom wouldn't work

    return (
        <ZoomProvider>
            <SyncZoomState />
            <SyncZoomTarget />

            <AnnotationToolProvider>
                <TransformZoomAnnotation>
                    <AnnotatorCanvasSettings>
                        <RawCanvas />
                    </AnnotatorCanvasSettings>
                </TransformZoomAnnotation>
            </AnnotationToolProvider>
        </ZoomProvider>
    );
};
