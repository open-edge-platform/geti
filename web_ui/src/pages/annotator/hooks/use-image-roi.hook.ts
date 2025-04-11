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
