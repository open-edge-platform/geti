// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { useCallback } from 'react';

import { useNavigate, useSearchParams } from 'react-router-dom';

import { isImage } from '../media/image.interface';
import { MediaItem } from '../media/media.interface';
import { isVideo, isVideoFrame } from '../media/video.interface';
import { DatasetIdentifier } from '../projects/dataset.interface';
import { paths } from '../../../packages/core/src/services/routes';

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

type AnnotatorTarget = {
    datasetIdentifier: DatasetIdentifier;
    mediaItem?: Pick<MediaItem, 'identifier'>;
    active?: boolean;
    taskId?: string | null;
};

export const useAnnotatorRoutePath = () => {
    const [searchParams] = useSearchParams();

    return useCallback(
        ({ datasetIdentifier, mediaItem, active, taskId }: AnnotatorTarget): string => {
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
                return `${mediaPath({ ...datasetIdentifier, mediaItem })}?${search}`;
            } else {
                return `${mediaPath({ ...datasetIdentifier, mediaItem })}`;
            }
        },
        [searchParams]
    );
};

export const useNavigateToAnnotatorRoute = () => {
    const navigate = useNavigate();
    const annotatorRoutePath = useAnnotatorRoutePath();

    return useCallback(
        ({ datasetIdentifier, mediaItem, active, taskId }: AnnotatorTarget) => {
            navigate(annotatorRoutePath({ datasetIdentifier, mediaItem, active, taskId }));
        },
        [navigate, annotatorRoutePath]
    );
};
