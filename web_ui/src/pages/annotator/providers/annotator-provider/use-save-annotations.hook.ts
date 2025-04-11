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

import { useEffect, useState } from 'react';

import { Annotation } from '../../../../core/annotations/annotation.interface';
import { getAnnotationsFromDTO } from '../../../../core/annotations/services/utils';
import { MediaItem } from '../../../../core/media/media.interface';
import { getAnnotationStatePerTaskFromDTO } from '../../../../core/media/services/utils';
import { useApplicationServices } from '../../../../core/services/application-services-provider.component';
import { useProject } from '../../../project-details/providers/project-provider/project-provider.component';
import { useDatasetIdentifier } from '../../hooks/use-dataset-identifier.hook';
import { useOptimisticallyUpdateAnnotationStatus } from '../dataset-provider/use-optimistically-update-annotation-status.hook';
import { useSelectedMediaItem } from '../selected-media-item-provider/selected-media-item-provider.component';

export const useSaveAnnotations = () => {
    const { project } = useProject();
    const datasetIdentifier = useDatasetIdentifier();
    const { selectedMediaItem } = useSelectedMediaItem();
    const { annotationService } = useApplicationServices();
    const [datasetIdentifierOfMediaItem, setDatasetIdentifierOfMediaItem] = useState(datasetIdentifier);

    useEffect(() => {
        setDatasetIdentifierOfMediaItem(datasetIdentifier);
        // eslint-disable-next-line react-hooks/exhaustive-deps
    }, [selectedMediaItem]);

    const optimisticallyUpdateAnnotationStatus = useOptimisticallyUpdateAnnotationStatus(datasetIdentifierOfMediaItem);

    return async (annotations: ReadonlyArray<Annotation>, mediaItem: MediaItem) => {
        const response = await annotationService.saveAnnotations(datasetIdentifier, mediaItem, annotations);

        const annotationStates = getAnnotationStatePerTaskFromDTO(response.annotation_state_per_task);

        const newAnnotations = getAnnotationsFromDTO(response.annotations, project.labels);

        optimisticallyUpdateAnnotationStatus(mediaItem, newAnnotations, annotationStates);

        return newAnnotations;
    };
};
