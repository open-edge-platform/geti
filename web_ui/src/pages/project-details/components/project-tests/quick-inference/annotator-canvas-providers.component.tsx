// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { ReactNode, useMemo } from 'react';

import { v4 as uuidv4 } from 'uuid';

import { Annotation } from '../../../../../core/annotations/annotation.interface';
import { MEDIA_TYPE } from '../../../../../core/media/base-media.interface';
import { getImageData, getImageDataUrl } from '../../../../../shared/canvas-utils';
import { AnnotatorProvider } from '../../../../annotator/providers/annotator-provider/annotator-provider.component';
import { RegionOfInterestProvider } from '../../../../annotator/providers/region-of-interest-provider/region-of-interest-provider.component';
import { DefaultSelectedMediaItemProvider } from '../../../../annotator/providers/selected-media-item-provider/default-selected-media-item-provider.component';
import { SelectedMediaItem } from '../../../../annotator/providers/selected-media-item-provider/selected-media-item.interface';
import { TaskProvider } from '../../../../annotator/providers/task-provider/task-provider.component';

// In this scenario we only care about the media item's image and annotations,
// all other props are not used for quick inference
const getFakeSelectedMediaItem = (image: ImageData, annotations: Annotation[]): SelectedMediaItem => {
    const sourceFromImageData = getImageDataUrl(image);

    return {
        identifier: { type: MEDIA_TYPE.IMAGE, imageId: uuidv4() },
        metadata: {
            height: image.height,
            width: image.width,
            size: 1234,
        },
        name: 'test',
        src: sourceFromImageData,
        thumbnailSrc: sourceFromImageData,
        uploadTime: '',
        uploaderId: '',
        annotationStatePerTask: [],
        image,
        annotations,
        predictions: undefined,
        lastAnnotatorId: null,
    };
};

interface AnnotatorCanvasProvidersProps {
    image: ImageData | undefined;
    annotations: Annotation[];
    children: ReactNode;
}

// This component contains providers that are required to render the annotator canvas
// The `DefaultSelectedMediaItemProvider` is used so that we don't call the annotations,
// predictions and image queries.
// Instead we provide a fixed media item.
export const AnnotatorCanvasProviders = ({ image, annotations, children }: AnnotatorCanvasProvidersProps) => {
    const selectedMediaItem: SelectedMediaItem = useMemo(() => {
        const img = image ?? getImageData(new Image());

        return getFakeSelectedMediaItem(img, annotations);
    }, [image, annotations]);

    return (
        <TaskProvider>
            <DefaultSelectedMediaItemProvider selectedMediaItem={selectedMediaItem}>
                <AnnotatorProvider>
                    <RegionOfInterestProvider>{children}</RegionOfInterestProvider>
                </AnnotatorProvider>
            </DefaultSelectedMediaItemProvider>
        </TaskProvider>
    );
};
