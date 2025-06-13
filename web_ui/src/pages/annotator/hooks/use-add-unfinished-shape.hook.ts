// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { useEffect, useRef } from 'react';

import { WatershedPolygon } from '@geti/smart-tools/src/watershed/interfaces';

import { Annotation } from '../../../core/annotations/annotation.interface';
import { Shape } from '../../../core/annotations/shapes.interface';
import { useAnnotationScene } from '../providers/annotation-scene-provider/annotation-scene-provider.component';
import { useSubmitAnnotations } from '../providers/submit-annotations-provider/submit-annotations-provider.component';

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
