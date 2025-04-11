// INTEL CONFIDENTIAL
//
// Copyright (C) 2023 Intel Corporation
//
// This software and the related documents are Intel copyrighted materials, and your use of them is governed by
// the express license under which they were provided to you ("License"). Unless the License provides otherwise,
// you may not use, modify, copy, publish, distribute, disclose or transmit this software or the related documents
// without Intel's prior written permission.
//
// This software and the related documents are provided as is, with no express or implied warranties,
// other than those that are expressly stated in the License.

import { MediaItem } from '../../../../core/media/media.interface';
import { DatasetIdentifier } from '../../../../core/projects/dataset.interface';
import { useNavigateToAnnotatorRoute } from '../../../../core/services/use-navigate-to-annotator-route.hook';
import { Button } from '../../button/button.component';

interface EditAnnotationsButtonProps {
    datasetIdentifier: DatasetIdentifier;
    mediaItem: MediaItem;
}

export const EditAnnotationsButton = ({ datasetIdentifier, mediaItem }: EditAnnotationsButtonProps): JSX.Element => {
    const navigate = useNavigateToAnnotatorRoute(datasetIdentifier);

    const goToAnnotator = () => {
        navigate({ ...datasetIdentifier, mediaItem });
    };

    return (
        <Button
            variant='secondary'
            onPress={goToAnnotator}
            id='edit-annotations'
            aria-label='Edit annotations'
            key='edit'
        >
            Edit
        </Button>
    );
};
