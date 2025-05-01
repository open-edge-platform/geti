// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { Loading } from '@shared/components/loading/loading.component';

import { isKeypointAnnotation } from '../../../../core/annotations/services/utils';
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
