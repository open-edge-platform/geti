// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

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
