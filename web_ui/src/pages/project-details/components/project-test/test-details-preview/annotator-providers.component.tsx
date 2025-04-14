// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { ReactNode, useMemo } from 'react';

import { Annotation } from '../../../../../core/annotations/annotation.interface';
import { MediaItem } from '../../../../../core/media/media.interface';
import { getImageData } from '../../../../../shared/canvas-utils';
import { AnnotatorCanvasSettings } from '../../../../annotator/annotator-settings.component';
import { AnnotatorProvider } from '../../../../annotator/providers/annotator-provider/annotator-provider.component';
import { RegionOfInterestProvider } from '../../../../annotator/providers/region-of-interest-provider/region-of-interest-provider.component';
import { DefaultSelectedMediaItemProvider } from '../../../../annotator/providers/selected-media-item-provider/default-selected-media-item-provider.component';
import { SelectedMediaItem } from '../../../../annotator/providers/selected-media-item-provider/selected-media-item.interface';
import { SyncZoomState, SyncZoomTarget } from '../../../../annotator/zoom/sync-zoom-state.component';
import { ZoomProvider } from '../../../../annotator/zoom/zoom-provider.component';

interface AnnotatorProvidersProps {
    mediaItem: MediaItem;
    image: ImageData | undefined;
    annotations: Annotation[];
    children: ReactNode;
}

export const AnnotatorProviders = ({ mediaItem, image, annotations, children }: AnnotatorProvidersProps) => {
    const selectedMediaItem: SelectedMediaItem = useMemo(() => {
        const defaultImage = new Image(mediaItem.metadata.width, mediaItem.metadata.height);

        return { ...mediaItem, image: image ?? getImageData(defaultImage), annotations, predictions: undefined };
    }, [mediaItem, image, annotations]);

    return (
        <DefaultSelectedMediaItemProvider selectedMediaItem={selectedMediaItem}>
            <AnnotatorProvider>
                <RegionOfInterestProvider>
                    <AnnotatorCanvasSettings>
                        <ZoomProvider>
                            <SyncZoomState />
                            <SyncZoomTarget />
                            {children}
                        </ZoomProvider>
                    </AnnotatorCanvasSettings>
                </RegionOfInterestProvider>
            </AnnotatorProvider>
        </DefaultSelectedMediaItemProvider>
    );
};
