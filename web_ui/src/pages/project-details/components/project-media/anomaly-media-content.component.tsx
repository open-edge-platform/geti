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

import { ComponentProps, Dispatch, useCallback, useMemo } from 'react';

import { Flex, Heading, View } from '@adobe/react-spectrum';
import isEmpty from 'lodash/isEmpty';
import { useNavigate } from 'react-router-dom';

import { MediaUploadAnomalousIcon, MediaUploadNormalIcon } from '../../../../assets/images';
import { Label } from '../../../../core/labels/label.interface';
import { isAnomalous, isExclusive } from '../../../../core/labels/utils';
import { paths } from '../../../../core/services/routes';
import { TUTORIAL_CARD_KEYS } from '../../../../core/user-settings/dtos/user-settings.interface';
import { DatasetMediaUploadActions } from '../../../../providers/media-upload-provider/media-upload-reducer-actions';
import {
    MEDIA_CONTENT_BUCKET,
    MediaUploadPerDataset,
    UploadMedia,
} from '../../../../providers/media-upload-provider/media-upload.interface';
import { TutorialCardBuilder } from '../../../../shared/components/tutorial-card/tutorial-card-builder.component';
import { useDatasetIdentifier } from '../../../annotator/hooks/use-dataset-identifier.hook';
import { MediaProvider, useMedia } from '../../../media/providers/media-provider.component';
import { getRequiredAnomalyFilters } from '../../../media/providers/utils';
import { MediaContentBucket } from './media-content-bucket.component';
import { getUploadingStatePerBucket } from './utils';

import classes from './media-content-bucket.module.scss';

interface AnomalyMediaContentProps {
    labels: Label[];
    mediaUploadState: MediaUploadPerDataset;
    dispatch: Dispatch<DatasetMediaUploadActions>;
    onUploadMedia: (uploadMedia: UploadMedia) => Promise<void>;
}

export const AnomalyMediaContent = ({
    labels,
    mediaUploadState,
    dispatch,
    onUploadMedia,
}: AnomalyMediaContentProps): JSX.Element => {
    const navigate = useNavigate();
    const datasetIdentifier = useDatasetIdentifier();

    const { uploadProgress } = mediaUploadState;

    // In this component we are 100% sure we have normal and anomaly label
    const normalLabel = useMemo((): Label => labels.find(isExclusive) as Label, [labels]);
    const normalMediaFilters = useMemo(() => {
        return getRequiredAnomalyFilters(normalLabel.id);
    }, [normalLabel]);

    const anomalousLabel = useMemo((): Label => labels.find(isAnomalous) as Label, [labels]);
    const anomalousMediaFilters = useMemo(() => {
        return getRequiredAnomalyFilters(anomalousLabel.id);
    }, [anomalousLabel]);

    const isLoadingNormalOverlayVisible = useCallback(
        (isMediaFetching: boolean): boolean => {
            return isMediaFetching || getUploadingStatePerBucket(uploadProgress, MEDIA_CONTENT_BUCKET.NORMAL);
        },
        [uploadProgress]
    );

    const isLoadingAnomalousOverlayVisible = useCallback(
        (isMediaFetching: boolean): boolean => {
            return isMediaFetching || getUploadingStatePerBucket(uploadProgress, MEDIA_CONTENT_BUCKET.ANOMALOUS);
        },
        [uploadProgress]
    );

    const isMediaDropVisible = useCallback(
        (bucket: MEDIA_CONTENT_BUCKET) =>
            (isMediaFetching: boolean, hasMediaItems: boolean, isMediaFilterEmpty: boolean): boolean => {
                const isUploadInProgress = getUploadingStatePerBucket(uploadProgress, bucket);

                if (isUploadInProgress && !hasMediaItems) {
                    return true;
                }

                const commonVisibility = !isMediaFetching && !hasMediaItems && isMediaFilterEmpty;

                return commonVisibility && !getUploadingStatePerBucket(uploadProgress, bucket);
            },
        [uploadProgress]
    );

    const uploadNormalMediaMetadata = useMemo(() => ({ dispatch, mediaUploadState }), [dispatch, mediaUploadState]);

    const uploadAnomalousMediaMetadata = useMemo(() => ({ dispatch, mediaUploadState }), [dispatch, mediaUploadState]);

    const handleUploadMediaCallback =
        (label: Label) =>
        (files: File[]): void => {
            onUploadMedia({
                datasetIdentifier,
                files,
                labelIds: [label.id],
                meta: isAnomalous(label) ? MEDIA_CONTENT_BUCKET.ANOMALOUS : MEDIA_CONTENT_BUCKET.NORMAL,
                label,
            });
        };

    return (
        <Flex flex={1} direction={'column'}>
            <TutorialCardBuilder cardKey={TUTORIAL_CARD_KEYS.PROJECT_DATASET_TUTORIAL} />
            <Flex flex={1} justifyContent='space-between' gap='size-200'>
                <View
                    flex={1}
                    overflow='hidden'
                    borderWidth='thin'
                    borderRadius='medium'
                    UNSAFE_style={{ borderColor: normalLabel.color, display: 'flex' }}
                >
                    <MediaProvider requiredFilters={normalMediaFilters} filterName='filter-normal'>
                        <MediaContentBucketWrapper
                            header={normalLabel.name}
                            DropBoxIcon={MediaUploadNormalIcon}
                            uploadMediaMetadata={uploadNormalMediaMetadata}
                            description={'Normal images are used for model training and evaluation'}
                            dropBoxIconSize='size-2400'
                            mediaBucket={MEDIA_CONTENT_BUCKET.NORMAL}
                            isLoadingOverlayVisible={isLoadingNormalOverlayVisible}
                            isMediaDropVisible={isMediaDropVisible(MEDIA_CONTENT_BUCKET.NORMAL)}
                            handleUploadMediaCallback={handleUploadMediaCallback(normalLabel)}
                            onCameraSelected={() =>
                                navigate(
                                    // eslint-disable-next-line max-len
                                    `${paths.project.dataset.camera(datasetIdentifier)}?defaultLabelId=${normalLabel.id}`
                                )
                            }
                        />
                    </MediaProvider>
                </View>
                <View
                    flex={1}
                    overflow='hidden'
                    borderWidth='thin'
                    borderRadius='medium'
                    UNSAFE_style={{ borderColor: anomalousLabel.color, display: 'flex' }}
                >
                    <MediaProvider requiredFilters={anomalousMediaFilters} filterName='filter-anomalous'>
                        <MediaContentBucketWrapper
                            header={anomalousLabel.name}
                            DropBoxIcon={MediaUploadAnomalousIcon}
                            uploadMediaMetadata={uploadAnomalousMediaMetadata}
                            dropBoxIconSize='size-2400'
                            description={'Anomalous images are used only for model evaluation'}
                            mediaBucket={MEDIA_CONTENT_BUCKET.ANOMALOUS}
                            isLoadingOverlayVisible={isLoadingAnomalousOverlayVisible}
                            isMediaDropVisible={isMediaDropVisible(MEDIA_CONTENT_BUCKET.ANOMALOUS)}
                            handleUploadMediaCallback={handleUploadMediaCallback(anomalousLabel)}
                            onCameraSelected={() =>
                                navigate(
                                    // eslint-disable-next-line max-len
                                    `${paths.project.dataset.camera(datasetIdentifier)}?defaultLabelId=${anomalousLabel.id}`
                                )
                            }
                            footerInfo={
                                <Heading
                                    margin={0}
                                    width='size-3600'
                                    level={4}
                                    UNSAFE_className={classes.footerAnomalousInfo}
                                >
                                    *Real examples of anomalous patterns will greatly improve finding the optimal
                                    threshold
                                </Heading>
                            }
                        />
                    </MediaProvider>
                </View>
            </Flex>
        </Flex>
    );
};

type MediaContentBucketWrapperProps = Omit<
    ComponentProps<typeof MediaContentBucket>,
    'contentBucketBodyClass' | 'contentBucketClass'
>;

function MediaContentBucketWrapper(props: MediaContentBucketWrapperProps): JSX.Element {
    const { media } = useMedia();
    const hasMediaItems = !isEmpty(media);

    return (
        <MediaContentBucket
            {...props}
            contentBucketBodyClass={hasMediaItems ? classes.mediaContentBody : classes.emptyMediaContentBody}
            contentBucketClass={hasMediaItems ? classes.mediaContentBucket : classes.emptyMediaContentBucket}
        />
    );
}
