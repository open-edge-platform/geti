// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { ListBox as AriaComponentsListBox, ListBoxItem, ListLayout, Virtualizer } from 'react-aria-components';

import { KeypointAnnotation } from '../../../../core/annotations/annotation.interface';
import { KeypointNode } from '../../../../core/annotations/shapes.interface';
import { ShapeType } from '../../../../core/annotations/shapetype.enum';
import { useAnnotationScene } from '../../providers/annotation-scene-provider/annotation-scene-provider.component';
import { NodeContent } from './node-content.component';

import styles from './node-list.module.scss';

interface NodeListProps {
    keypointAnnotation: KeypointAnnotation;
}

export const NodeList = ({ keypointAnnotation }: NodeListProps) => {
    const { updateAnnotation } = useAnnotationScene();

    const points = keypointAnnotation.shape.points
        .map((point) => ({ ...point, id: `${point.label.id}-${point.x}-${point.y}` }))
        .reverse();

    const handleUpdateAnnotation = (newPoint: KeypointNode) => {
        updateAnnotation({
            ...keypointAnnotation,
            shape: {
                shapeType: ShapeType.Pose,
                points: keypointAnnotation.shape.points.map((currentPoint) =>
                    currentPoint.label.id === newPoint.label.id ? newPoint : currentPoint
                ),
            },
        });
    };

    return (
        <Virtualizer layout={ListLayout}>
            <AriaComponentsListBox aria-label='Virtualized ListBox' items={points} className={styles.container}>
                {(point) => (
                    <ListBoxItem textValue={point.label.name}>
                        <NodeContent
                            point={point}
                            isLast={point.id === points.at(-1)?.id}
                            onUpdate={handleUpdateAnnotation}
                        />
                    </ListBoxItem>
                )}
            </AriaComponentsListBox>
        </Virtualizer>
    );
};
