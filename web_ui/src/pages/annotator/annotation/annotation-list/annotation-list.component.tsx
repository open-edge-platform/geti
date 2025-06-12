// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { useMemo } from 'react';

import {
    AriaComponentsListBox,
    Content,
    DropIndicator,
    ListBoxItem,
    ListLayout,
    Loading,
    useDragAndDrop,
    Virtualizer,
} from '@geti/ui';

import { Annotation } from '../../../../core/annotations/annotation.interface';
import { hasEqualId } from '../../../../shared/utils';
import { useIsSceneBusy } from '../../hooks/use-annotator-scene-interaction-state.hook';
import { useAnnotationToolContext } from '../../providers/annotation-tool-provider/annotation-tool-provider.component';
import { AnnotationListItemContent } from './annotation-list-item/annotation-list-item-content.component';
import { reorder } from './utils';

import styles from './annotation-list.module.scss';

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

    const { dragAndDropHooks } = useDragAndDrop({
        isDisabled: isSceneBusy || isDragDisabled,

        renderDropIndicator: (target) => {
            return <DropIndicator target={target} className={styles.dropTarget} />;
        },
        getItems: (keys) => {
            return [...keys].map((key) => ({
                'text/plain': reversedAnnotations.find(hasEqualId(String(key)))?.id ?? '',
            }));
        },
        onReorder: ({ keys, target }) => {
            const arrayKeys = keys.keys().toArray();
            const sourceKey = arrayKeys.at(0)?.toString() ?? '';
            const sourceIndex = reversedAnnotations.findIndex(hasEqualId(sourceKey));
            const destinationIndex = reversedAnnotations.findIndex(hasEqualId(String(target.key)));
            const reorderedAnnotations = reorder(reversedAnnotations, sourceIndex, destinationIndex);

            annotationToolContext.scene.replaceAnnotations(reorderedAnnotations);
        },
    });

    if (isLoading) {
        return (
            <Content position={'relative'} UNSAFE_style={{ height: '100%' }}>
                <Loading size='M' />
            </Content>
        );
    }

    return (
        <Virtualizer layout={ListLayout}>
            <AriaComponentsListBox
                id='annotation-list'
                aria-label='Annotations list'
                items={reversedAnnotations}
                className={styles.container}
                dragAndDropHooks={dragAndDropHooks}
            >
                {(annotation) => (
                    <ListBoxItem textValue={annotation.id} className={styles.draggable}>
                        <AnnotationListItemContent
                            key={annotation.id}
                            annotation={annotation}
                            isLast={annotation.id === reversedAnnotations.at(-1)?.id}
                            annotationToolContext={annotationToolContext}
                        />
                    </ListBoxItem>
                )}
            </AriaComponentsListBox>
        </Virtualizer>
    );
};
