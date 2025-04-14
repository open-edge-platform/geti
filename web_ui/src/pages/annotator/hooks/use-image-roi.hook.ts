// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

// without Intel's prior written permission.
//
// This software and the related documents are provided as is, with no express or implied warranties,
// other than those that are expressly stated in the License.

import { useMemo } from 'react';

import { Rect } from '../../../core/annotations/shapes.interface';
import { ShapeType } from '../../../core/annotations/shapetype.enum';
import { useSelectedMediaItem } from '../providers/selected-media-item-provider/selected-media-item-provider.component';

export const useImageROI = (): Rect | undefined => {
    const { selectedMediaItem } = useSelectedMediaItem();
    const image = selectedMediaItem?.image;

    return useMemo(() => {
        if (image) {
            return { x: 0, y: 0, width: image.width, height: image.height, shapeType: ShapeType.Rect };
        }

        return undefined;
    }, [image]);
};
