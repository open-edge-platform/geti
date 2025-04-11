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
