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

import { useEffect } from 'react';

import { isKeypointDetection } from '../../../../../core/projects/domains';
import { Accordion } from '../../../../../shared/components/accordion/accordion.component';
import { AnnotationListContainer } from '../../../annotation/annotation-list/annotation-list-container/annotation-list-container.component';
import { PoseListContainer } from '../../../annotation/pose-list/pose-list-container.component';
import { useSelectedMediaItem } from '../../../providers/selected-media-item-provider/selected-media-item-provider.component';
import { useSelected } from '../../../providers/selected-provider/selected-provider.component';
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
