// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { DatasetIdentifier } from '../../projects/dataset.interface';
import { MEDIA_ANNOTATION_STATUS } from '../base.interface';
import { MediaItemDTO } from '../dtos/media.interface';
import { getMediaItemFromDTO } from './utils';

const buildImageSrc = (
    datasetIdentifier: DatasetIdentifier,
    videoId: string,
    frameNumber: number,
    type: 'thumb' | 'full'
): string => {
    const { organizationId, workspaceId, projectId, datasetId } = datasetIdentifier;

    return `/api/v1/organizations/${organizationId}/workspaces/${workspaceId}/projects/${projectId}/datasets/${datasetId}/media/videos/${videoId}/frames/${frameNumber}/display/${type}`;
};

describe('getMediaItemFromDTO', () => {
    it('gets a media item from a video frame dto', () => {
        const size = 12345;
        const mediaDTO: MediaItemDTO = {
            id: '30',
            media_information: {
                display_url:
                    '/api/v1/workspaces/623b014a948d4113fc31e06c/projects/62471025948d4113fc31f253/datasets/62471025948d4113fc31f252/media/videos/62471039948d4113fc31f25f/frames/30/display/full',
                duration: 10,
                frame_stride: 30,
                frame_count: 300,
                frame_rate: 30,
                height: 720,
                width: 1280,
                video_id: '62471039948d4113fc31f25f',
                size,
            },
            name: 'Trailcam footage of a Pine Marten and wild Fallow Deer (1)_f30',
            thumbnail:
                '/api/v1/workspaces/623b014a948d4113fc31e06c/projects/62471025948d4113fc31f253/datasets/62471025948d4113fc31f252/media/videos/62471039948d4113fc31f25f/frames/30/display/thumb',
            type: 'video_frame',
            upload_time: '2022-04-01T14:46:17.244000+00:00',
            uploader_id: '9b89482b-3894-41a1-a67c-7d1fbe8d47ad',
            annotation_state_per_task: [],
            state: MEDIA_ANNOTATION_STATUS.NONE,
            frame_index: 0,
            last_annotator_id: null,
        };

        const datasetIdentifier = {
            workspaceId: '623b014a948d4113fc31e06c',
            projectId: '62471025948d4113fc31f253',
            datasetId: '62471025948d4113fc31f252',
            organizationId: 'organization-id',
        };
        const mediaItem = getMediaItemFromDTO(datasetIdentifier, mediaDTO);

        expect(mediaItem).toEqual({
            identifier: {
                frameNumber: 30,
                type: 'video_frame',
                videoId: '62471039948d4113fc31f25f',
            },
            annotationSceneId: undefined,
            annotationStatePerTask: [],
            lastAnnotatorId: null,
            metadata: {
                duration: 10,
                fps: 30,
                frameStride: 30,
                frames: 300,
                height: 720,
                width: 1280,
                size,
            },
            name: 'Trailcam footage of a Pine Marten and wild Fallow Deer (1)_f30',
            src: buildImageSrc(
                datasetIdentifier,
                mediaDTO.media_information.video_id,
                mediaDTO.media_information.frame_rate,
                'full'
            ),
            status: MEDIA_ANNOTATION_STATUS.NONE,
            thumbnailSrc: buildImageSrc(
                datasetIdentifier,
                mediaDTO.media_information.video_id,
                mediaDTO.media_information.frame_rate,
                'thumb'
            ),
            uploadTime: '2022-04-01T14:46:17.244000+00:00',
            uploaderId: '9b89482b-3894-41a1-a67c-7d1fbe8d47ad',
        });
    });
});
