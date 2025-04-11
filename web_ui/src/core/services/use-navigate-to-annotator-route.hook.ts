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

import { useCallback } from 'react';

import { useNavigate, useSearchParams } from 'react-router-dom';

import { isImage } from '../media/image.interface';
import { MediaItem } from '../media/media.interface';
import { isVideo, isVideoFrame } from '../media/video.interface';
import { ProjectIdentifier } from '../projects/core.interface';
import { paths } from './routes';

const mediaPath = ({
    organizationId,
    workspaceId,
    projectId,
    datasetId,
    mediaItem,
}: {
    organizationId: string;
    workspaceId: string;
    projectId: string;
    datasetId: string;
    mediaItem?: Pick<MediaItem, 'identifier'>;
}) => {
    if (mediaItem === undefined) {
        return paths.project.annotator.index({ organizationId, workspaceId, projectId, datasetId });
    }

    if (isImage(mediaItem)) {
        const { imageId } = mediaItem.identifier;

        return paths.project.annotator.image({ organizationId, workspaceId, imageId, datasetId, projectId });
    }

    if (isVideo(mediaItem)) {
        const { videoId } = mediaItem.identifier;

        return paths.project.annotator.video({ organizationId, workspaceId, videoId, datasetId, projectId });
    }

    if (isVideoFrame(mediaItem)) {
        const { videoId, frameNumber } = mediaItem.identifier;
        return paths.project.annotator.videoFrame({
            organizationId,
            workspaceId,
            projectId,
            datasetId,
            videoId,
            frameNumber: `${frameNumber}`,
        });
    }

    return paths.project.annotator.index({ organizationId, workspaceId, projectId, datasetId });
};

export type NavigateToAnnotatorRoute = ({
    datasetId,
    mediaItem,
    active,
    taskId,
}: {
    datasetId: string;
    mediaItem?: Pick<MediaItem, 'identifier'>;
    active?: boolean;
    taskId?: string | null;
}) => void;

export const useNavigateToAnnotatorRoute = (projectIdentifier: ProjectIdentifier): NavigateToAnnotatorRoute => {
    const [searchParams] = useSearchParams();
    const navigate = useNavigate();

    return useCallback(
        ({ datasetId, mediaItem, active, taskId }) => {
            const { workspaceId, projectId, organizationId } = projectIdentifier;

            if (active !== undefined) {
                if (active === true) {
                    searchParams.set('active', 'true');
                } else {
                    searchParams.delete('active');
                }
            }

            if (taskId !== undefined) {
                if (taskId !== null) {
                    searchParams.set('task-id', taskId);
                } else {
                    searchParams.delete('task-id');
                }
            }

            searchParams.delete('annotations-filter');

            const search = searchParams.toString();

            if (search !== '') {
                navigate(`${mediaPath({ organizationId, workspaceId, projectId, datasetId, mediaItem })}?${search}`);
            } else {
                navigate(`${mediaPath({ organizationId, workspaceId, projectId, datasetId, mediaItem })}`);
            }
        },
        [navigate, projectIdentifier, searchParams]
    );
};
