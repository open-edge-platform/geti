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

import { ReactNode } from 'react';

import { Heading, Text } from '@adobe/react-spectrum';

import { MEDIA_CONTENT_BUCKET } from '../../../providers/media-upload-provider/media-upload.interface';
import { VALID_IMAGE_TYPES, VALID_VIDEO_TYPES } from '../../media-utils';

import classes from './media-drop-box.module.scss';

interface MediaDropBoxHeaderProps {
    formats: string[];
    isMultipleUpload?: boolean;
    bucket?: MEDIA_CONTENT_BUCKET;
}

const BUCKET_NAME_MAPPING: Record<MEDIA_CONTENT_BUCKET, string | undefined> = {
    [MEDIA_CONTENT_BUCKET.GENERIC]: undefined,
    [MEDIA_CONTENT_BUCKET.ANOMALOUS]: 'anomalous*',
    [MEDIA_CONTENT_BUCKET.NORMAL]: 'normal',
};

const AnomalyHeader = ({ children }: { children: ReactNode }) => (
    <Text
        id={'media-drop-box-header-id'}
        data-testid={'media-drop-box-header-id'}
        UNSAFE_className={classes.anomalyMediaDropBoxHeader}
        width={'size-2400'}
    >
        {children}
    </Text>
);

const GenericHeader = ({ children }: { children: ReactNode }) => (
    <Heading
        id={'media-drop-box-header-id'}
        data-testid={'media-drop-box-header-id'}
        margin={0}
        UNSAFE_className={classes.mediaDropBoxTitle}
    >
        {children}
    </Heading>
);

export const MediaDropBoxHeader = ({
    formats,
    isMultipleUpload = true,
    bucket = MEDIA_CONTENT_BUCKET.GENERIC,
}: MediaDropBoxHeaderProps) => {
    const VALID_VIDEO_TYPES_LOWERCASE = VALID_VIDEO_TYPES.map((ext) => ext.toLocaleLowerCase());

    const isVideoFormat = formats.some((extension) => VALID_VIDEO_TYPES_LOWERCASE.includes(extension));

    const VALID_IMAGE_TYPES_LOWERCASE = VALID_IMAGE_TYPES.map((ext) => ext.toLocaleLowerCase());

    const isImageFormat = formats.some((extension) => VALID_IMAGE_TYPES_LOWERCASE.includes(extension));

    const bucketName = BUCKET_NAME_MAPPING[bucket];

    if (bucket === MEDIA_CONTENT_BUCKET.GENERIC) {
        if (isImageFormat && isVideoFormat && isMultipleUpload) {
            return <GenericHeader>Drag and drop images and videos</GenericHeader>;
        }

        if (!isVideoFormat) {
            return <GenericHeader>Drag and drop image</GenericHeader>;
        }

        return <GenericHeader>Drag and drop image and video</GenericHeader>;
    }

    if (isImageFormat && isVideoFormat && isMultipleUpload) {
        return (
            <AnomalyHeader>
                Drag and drop{' '}
                {bucketName && <Text UNSAFE_className={classes.mediaDropBoxBucketName}>{bucketName} </Text>}
                images and videos
            </AnomalyHeader>
        );
    }

    if (!isVideoFormat) {
        return (
            <AnomalyHeader>
                Drag and drop{' '}
                {bucketName && <Text UNSAFE_className={classes.mediaDropBoxBucketName}>{bucketName} </Text>}image
            </AnomalyHeader>
        );
    }

    return (
        <AnomalyHeader>
            Drag and drop {bucketName && <Text UNSAFE_className={classes.mediaDropBoxBucketName}>{bucketName} </Text>}
            image and video
        </AnomalyHeader>
    );
};
