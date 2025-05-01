// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { useMemo } from 'react';

import { Content } from '@adobe/react-spectrum';
import { Loading } from '@shared/components/loading/loading.component';
import {
    DragDropContext,
    Draggable,
    DraggableChildrenFn,
    DraggableProvided,
    Droppable,
    DroppableProvided,
    DropResult,
} from 'react-beautiful-dnd';
import { Virtuoso } from 'react-virtuoso';

import { Annotation } from '../../../../core/annotations/annotation.interface';
import { ThemeProvider } from '../../../../theme/theme-provider.component';
import { AnnotationToolContext } from '../../core/annotation-tool-context.interface';
import { useIsSceneBusy } from '../../hooks/use-annotator-scene-interaction-state.hook';
import { useAnnotationToolContext } from '../../providers/annotation-tool-provider/annotation-tool-provider.component';
import { HeightPreservingItem } from '../height-preserving-item.component';
import { AnnotationListItemContent } from './annotation-list-item/annotation-list-item-content.component';
import { reorder } from './utils';

interface DraggableAnnotationProps {
    provided: DraggableProvided;
    annotation: Annotation;
    annotationToolContext: AnnotationToolContext;
    isDragging: boolean;
    isLast: boolean;
}

const DraggableAnnotation = ({
    provided,
    annotation,
    isDragging,
    isLast,
    annotationToolContext,
}: DraggableAnnotationProps) => {
    return (
        <ThemeProvider>
            <div
                {...provided.draggableProps}
                {...provided.dragHandleProps}
                ref={provided.innerRef}
                style={provided.draggableProps.style}
                className={`item ${isDragging ? 'is-dragging' : ''}`}
            >
                <AnnotationListItemContent
                    key={annotation.id}
                    annotation={annotation}
                    isLast={isLast}
                    isDragging={isDragging}
                    annotationToolContext={annotationToolContext}
                />
            </div>
        </ThemeProvider>
    );
};

interface AnnotationListProps {
    isLoading?: boolean;
    annotations: Annotation[];
    isDragDisabled?: boolean;
}

export const AnnotationList = ({ annotations, isLoading, isDragDisabled }: AnnotationListProps) => {
    const isSceneBusy = useIsSceneBusy();
    const annotationToolContext = useAnnotationToolContext();

    const reversedAnnotations = useMemo(() => {
        return [...annotations].reverse();
    }, [annotations]);

    const handleDragEnd = (result: DropResult): void => {
        if (result.destination && result.destination.index !== result.source.index) {
            const { destination, source } = result;
            const reorderedAnnotations: Annotation[] = reorder(reversedAnnotations, source.index, destination.index);

            // Since we reordered the annotations based on reversed annotations,
            // we have to reverse them again so that we store the annotations
            // in the proper order
            annotationToolContext.scene.replaceAnnotations(reorderedAnnotations);
        }
    };

    const renderClone: DraggableChildrenFn = (provided, snapshot, rubric) => {
        const index = rubric.source.index;
        const annotation = reversedAnnotations[index];

        return (
            <DraggableAnnotation
                provided={provided}
                isDragging={snapshot.isDragging}
                isLast={false}
                annotation={annotation}
                annotationToolContext={annotationToolContext}
            />
        );
    };

    if (isLoading) {
        return (
            <Content position={'relative'} UNSAFE_style={{ height: '100%' }}>
                <Loading size='M' id={'annotation-list-loader'} />
            </Content>
        );
    }

    // We use react beautiful dnd in combination with virtual rendering via Virtuoso to make the
    // annotation list both draggable and virtual.
    // For more information and examples see:
    // https://github.com/atlassian/react-beautiful-dnd/blob/master/docs/patterns/virtual-lists.md
    // https://virtuoso.dev/react-beautiful-dnd/
    return (
        <DragDropContext onDragEnd={handleDragEnd}>
            <Droppable droppableId='annotation-droppable-id' mode='virtual' renderClone={renderClone}>
                {(provided: DroppableProvided) => {
                    return (
                        <Virtuoso<Annotation>
                            role='list'
                            aria-label='Annotations list'
                            components={{ Item: HeightPreservingItem }}
                            id='annotation-list'
                            // @ts-expect-error innerRef does not contain Window, which is fine
                            scrollerRef={provided.innerRef}
                            data={reversedAnnotations}
                            itemContent={(index, annotation) => {
                                return (
                                    <Draggable
                                        draggableId={annotation.id}
                                        index={index}
                                        key={annotation.id}
                                        isDragDisabled={isSceneBusy || isDragDisabled}
                                    >
                                        {(draggableProvided) => (
                                            <DraggableAnnotation
                                                provided={draggableProvided}
                                                annotation={annotation}
                                                isDragging={false}
                                                isLast={index === reversedAnnotations.length - 1}
                                                annotationToolContext={annotationToolContext}
                                            />
                                        )}
                                    </Draggable>
                                );
                            }}
                        />
                    );
                }}
            </Droppable>
        </DragDropContext>
    );
};
