// INTEL CONFIDENTIAL
//
// Copyright (C) 2024 Intel Corporation
//
// This software and the related documents are Intel copyrighted materials, and your use of them is governed by
// the express license under which they were provided to you ("License"). Unless the License provides otherwise,
// you may not use, modify, copy, publish, distribute, disclose or transmit this software or the related documents
// without Intel's prior written permission.
//
// This software and the related documents are provided as is, with no express or implied warranties,
// other than those that are expressly stated in the License.

import { isKeypointAnnotation } from '../../../../core/annotations/services/utils';
import { Loading } from '../../../../shared/components/loading/loading.component';
import { useAnnotatorMode } from '../../hooks/use-annotator-mode';
import { useLocalAnnotations } from '../../hooks/use-local-annotations.hooks';
import { useLocalPredictions } from '../../hooks/use-local-predictions.hooks';
import { PaneList } from '../pane-list.component';
import { NodeList } from './node-list.component';
import { PoseListActions } from './pose-list-actions.component';

export const PoseListContainer = () => {
    const annotations = useLocalAnnotations();
    const { predictions, isFetching } = useLocalPredictions();
    const { isActiveLearningMode } = useAnnotatorMode();

    const isLoading = !isActiveLearningMode && isFetching;
    const finalAnnotations = isActiveLearningMode ? annotations : predictions;
    const keypointAnnotation = finalAnnotations.find(isKeypointAnnotation);

    if (!keypointAnnotation) {
        return <></>;
    }

    return (
        <PaneList
            listActions={<PoseListActions keypointAnnotation={keypointAnnotation} />}
            itemsList={isLoading ? <Loading size='M' /> : <NodeList keypointAnnotation={keypointAnnotation} />}
        />
    );
};
