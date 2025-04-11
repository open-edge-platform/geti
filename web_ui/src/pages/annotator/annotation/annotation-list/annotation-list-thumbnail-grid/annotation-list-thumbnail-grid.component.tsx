// INTEL CONFIDENTIAL
//
// Copyright (C) 2021 Intel Corporation
//
// This software and the related documents are Intel copyrighted materials, and your use of them is governed by
// the express license under which they were provided to you ("License"). Unless the License provides otherwise,
// you may not use, modify, copy, publish, distribute, disclose or transmit this software or the related documents
// without Intel's prior written permission.
//
// This software and the related documents are provided as is, with no express or implied warranties,
// other than those that are expressly stated in the License.

import { useMemo } from 'react';

import { Grid, repeat, View } from '@adobe/react-spectrum';
import isEmpty from 'lodash/isEmpty';
import sortBy from 'lodash/sortBy';

import { TaskChainInput } from '../../../../../core/annotations/annotation.interface';
import { MEDIA_ANNOTATION_STATUS } from '../../../../../core/media/base.interface';
import { useROI } from '../../../providers/region-of-interest-provider/region-of-interest-provider.component';
import { AnnotationListItemThumbnail } from '../annotation-list-item/annotation-list-item-thumbnail.component';
import { EmptyAnnotationsGrid } from './empty-annotations-grid.component';

import classes from './annotation-list-thumbnail-grid.module.scss';

interface AnnotationListThumbnailGridProps {
    annotations: ReadonlyArray<TaskChainInput>;
    onSelectAnnotation: (annotationId: string) => (isSelected: boolean) => void;
}

export const AnnotationListThumbnailGrid = ({
    annotations,
    onSelectAnnotation,
}: AnnotationListThumbnailGridProps): JSX.Element => {
    const { image } = useROI();

    const thumbnails = useMemo(
        () =>
            // Sort annotations by descending zIndex so that next and previous buttons behave consistently
            sortBy(annotations, ({ zIndex }) => -zIndex).map((annotation) => {
                const status = isEmpty(annotation.outputs)
                    ? MEDIA_ANNOTATION_STATUS.NONE
                    : MEDIA_ANNOTATION_STATUS.ANNOTATED;

                return (
                    <AnnotationListItemThumbnail
                        key={`annotation-grid-item-${annotation.id}`}
                        annotationId={annotation.id}
                        annotationShape={annotation.shape}
                        image={image}
                        isSelected={annotation.isSelected}
                        onSelectAnnotation={onSelectAnnotation(annotation.id)}
                        status={status}
                    />
                );
            }),

        // eslint-disable-next-line react-hooks/exhaustive-deps
        [annotations]
    );

    return (
        <View UNSAFE_className={classes.gridWrapper} data-testid={'annotation-list-thumbnail-grid'}>
            {isEmpty(annotations) ? (
                <EmptyAnnotationsGrid />
            ) : (
                <Grid columns={{ base: repeat(3, '1fr'), L: repeat(4, '1fr') }} justifyItems={'center'} gap={'size-50'}>
                    {thumbnails}
                </Grid>
            )}
        </View>
    );
};
