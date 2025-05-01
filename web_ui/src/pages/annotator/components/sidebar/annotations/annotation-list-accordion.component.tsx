// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { useEffect } from 'react';

import { Accordion } from '@shared/components/accordion/accordion.component';

import { isKeypointDetection } from '../../../../../core/projects/domains';
import { useSelected } from '../../../../../providers/selected-provider/selected-provider.component';
import { AnnotationListContainer } from '../../../annotation/annotation-list/annotation-list-container/annotation-list-container.component';
import { PoseListContainer } from '../../../annotation/pose-list/pose-list-container.component';
import { useSelectedMediaItem } from '../../../providers/selected-media-item-provider/selected-media-item-provider.component';
import { useTask } from '../../../providers/task-provider/task-provider.component';
import { AnnotationsHeader } from './annotations-header.component';

const useResetSelection = () => {
    const { setSelected } = useSelected();
    const { selectedMediaItem } = useSelectedMediaItem();

    useEffect(() => {
        setSelected([]);
        // eslint-disable-next-line react-hooks/exhaustive-deps
    }, [selectedMediaItem]);
};

export const AnnotationListAccordion = (): JSX.Element => {
    const { selectedTask } = useTask();
    const isKeypointTask = selectedTask && isKeypointDetection(selectedTask.domain);

    useResetSelection();

    return (
        <Accordion
            defaultOpenState
            height={'100%'}
            padding={'size-150'}
            overflow={'hidden'}
            idPrefix={'annotation-list'}
            backgroundColor={'gray-200'}
            data-testid={'annotation-list-accordion'}
            hasFoldButton={false}
            header={<AnnotationsHeader />}
        >
            {isKeypointTask ? <PoseListContainer /> : <AnnotationListContainer />}
        </Accordion>
    );
};
