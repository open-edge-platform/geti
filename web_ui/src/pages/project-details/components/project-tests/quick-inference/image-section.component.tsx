// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { CSSProperties } from 'react';

import { View } from '@geti/ui';
import { identity } from 'lodash-es';

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
