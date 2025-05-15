// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { MediaItem } from '../../../../core/media/media.interface';
import { DatasetIdentifier } from '../../../../core/projects/dataset.interface';
import { useAnnotatorRoutePath } from '../../../../core/services/use-navigate-to-annotator-route.hook';
import { Button } from '../../button/button.component';

interface EditAnnotationsButtonProps {
    datasetIdentifier: DatasetIdentifier;
    mediaItem: MediaItem;
}

export const EditAnnotationsButton = ({ datasetIdentifier, mediaItem }: EditAnnotationsButtonProps): JSX.Element => {
    const href = useAnnotatorRoutePath()({ datasetIdentifier, mediaItem });

    return (
        <Button variant='secondary' href={href} id='edit-annotations' aria-label='Edit annotations' key='edit'>
            Edit
        </Button>
    );
};
