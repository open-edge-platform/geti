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

import { useEffect, useRef } from 'react';

import { Annotation } from '../../../core/annotations/annotation.interface';
import { Shape } from '../../../core/annotations/shapes.interface';
import { useAnnotationScene } from '../providers/annotation-scene-provider/annotation-scene-provider.component';
import { useSubmitAnnotations } from '../providers/submit-annotations-provider/submit-annotations-provider.component';
import { WatershedPolygon } from '../tools/watershed-tool/watershed-tool.interface';

interface useAddUnfinishedShapeProps {
    reset: () => void;
    shapes: Shape[] | WatershedPolygon[];
    addShapes: (shape: Shape[] | WatershedPolygon[]) => Annotation[];
}

export const useAddUnfinishedShape = ({ addShapes, shapes, reset }: useAddUnfinishedShapeProps): void => {
    const prevShape = useRef<Shape[] | WatershedPolygon[] | null>(null);
    const { setUnfinishedShapeCallback } = useSubmitAnnotations();
    const { annotations } = useAnnotationScene();

    useEffect(() => {
        return () => {
            if (prevShape?.current?.length) {
                addShapes(prevShape.current);
            }

            setUnfinishedShapeCallback(null);
        };
        // eslint-disable-next-line react-hooks/exhaustive-deps
    }, []);

    useEffect(() => {
        if (shapes.length) {
            setUnfinishedShapeCallback((): Annotation[] => {
                reset();

                const newAnnotations = addShapes(shapes);

                return [...annotations, ...newAnnotations];
            });
        } else {
            setUnfinishedShapeCallback(null);
        }

        prevShape.current = shapes;

        // eslint-disable-next-line react-hooks/exhaustive-deps
    }, [shapes]);
};
