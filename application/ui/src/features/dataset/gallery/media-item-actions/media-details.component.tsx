// Copyright (C) 2026 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

import { $api } from '@/api';
import type { Media } from '@/api/types';
import { formatCompactDuration } from '@/components/media-thumbnail/util';
import { useTranslation } from '@/i18n';
import { Button, ButtonGroup, Content, Dialog, Heading } from '@geti-ui/ui';
import { useQuery } from '@tanstack/react-query';
import { useProjectIdentifier } from 'hooks/use-project-identifier.hook';
import { useNumberFormatter } from 'react-aria';

import { annotationsQueryOptions } from '../../../../modules/annotator/shell/api/use-annotations-query';
import { EMPTY_LABEL_ID } from '../../../../shared/labels';
import { isVideo } from '../../../../shared/media-item-utils';
import { getThumbnailUrl } from '../../../../shared/media-url.utils';
import { formatBytes } from '../../../../shared/util';

import classes from './media-details.module.scss';

type MediaDetailsProps = {
    item: Media;
    onClose: () => void;
};

export const MediaDetails = ({ item, onClose }: MediaDetailsProps) => {
    const { t } = useTranslation();
    const projectId = useProjectIdentifier();
    const number = useNumberFormatter({ maximumFractionDigits: 2 });
    const mediaFileName = `${item.name}.${item.format}`;
    const isVideoItem = isVideo(item);
    const hasAnnotations = item.annotation_status.has_annotations;
    const annotationsQuery = useQuery({
        ...annotationsQueryOptions(projectId, item),
        enabled: !isVideoItem && hasAnnotations,
    });
    const framesQuery = $api.useQuery(
        'get',
        '/api/projects/{project_id}/dataset/media/{media_id}/frames',
        {
            params: {
                path: { project_id: projectId, media_id: item.id },
                // The API defaults to a limited frame range; video totals need every frame, including the last one.
                query: isVideoItem
                    ? { frame_index_from: 0, frame_index_to: Math.max(0, item.frame_count - 1) }
                    : undefined,
            },
        },
        { enabled: isVideoItem && hasAnnotations }
    );
    const query = isVideoItem ? framesQuery : annotationsQuery;
    const hasError = hasAnnotations && query.isError;
    const savedAnnotations = isVideoItem
        ? framesQuery.data?.flatMap((frame) => frame.annotation_data.annotations)
        : annotationsQuery.data?.annotations;
    const annotationCount = isVideoItem
        ? (framesQuery.data?.reduce(
              (total, { annotation_data }) =>
                  total + (annotation_data.annotations.length || (annotation_data.user_reviewed ? 1 : 0)),
              0
          ) ?? 0)
        : (savedAnnotations?.length ?? 0);
    // Count No object/No label as a distinct category, as DatasetLabelsChart does.
    // Unlike this count, MediaFilterLabels only lists project labels, excluding the empty label.
    // Image queries normalize empty annotations to EMPTY_LABEL_ID; video frames need it added explicitly.
    const labelIds = new Set(savedAnnotations?.flatMap((annotation) => annotation.labels.map((label) => label.id)));
    if (
        isVideoItem &&
        framesQuery.data?.some(
            ({ annotation_data }) => annotation_data.user_reviewed && annotation_data.annotations.length === 0
        )
    ) {
        labelIds.add(EMPTY_LABEL_ID);
    }
    const labelCount = labelIds.size;
    const annotationValue = (value: number) =>
        !hasAnnotations
            ? number.format(0)
            : query.isPending
              ? t('dataset.mediaDetails.loading')
              : hasError
                ? t('dataset.mediaDetails.unavailable')
                : number.format(value);
    const status = t(hasAnnotations ? 'dataset.statistics.annotated' : 'dataset.statistics.unannotated');
    const fields = [
        [t('dataset.mediaDetails.resolution'), `${item.width} × ${item.height} px`],
        [t('dataset.mediaDetails.fileSize'), formatBytes(item.size)],
        [t('dataset.mediaDetails.format'), item.format.toUpperCase()],
        [t('dataset.mediaDetails.type'), t(isVideoItem ? 'dataset.mediaDetails.video' : 'dataset.mediaDetails.image')],
        ...(isVideoItem
            ? [
                  [t('dataset.mediaDetails.frameRate'), `${number.format(item.fps)} FPS`],
                  [t('dataset.mediaDetails.duration'), formatCompactDuration(item.duration)],
                  [t('dataset.mediaDetails.frames'), number.format(item.frame_count)],
                  [
                      t('dataset.mediaDetails.annotatedFrames'),
                      number.format(item.annotation_status.annotated_video_frames),
                  ],
              ]
            : []),
        [t('dataset.mediaDetails.annotations'), annotationValue(annotationCount)],
        [t('dataset.mediaDetails.labels'), annotationValue(labelCount)],
    ];

    return (
        <Dialog width='1000px'>
            <Heading>{t('dataset.mediaDetails.title')}</Heading>
            <Content UNSAFE_className={classes.content}>
                <div className={classes.layout}>
                    <div className={classes.preview}>
                        <img src={getThumbnailUrl(projectId, item.id)} alt={item.name} />
                    </div>
                    <div className={classes.details}>
                        <h3 className={classes.name} title={mediaFileName}>
                            {mediaFileName}
                        </h3>
                        <span className={classes.status} role='status'>
                            {status}
                        </span>
                        <dl className={classes.fields}>
                            {fields.map(([label, value]) => (
                                <div key={label}>
                                    <dt>{label}</dt>
                                    <dd>{value}</dd>
                                </div>
                            ))}
                        </dl>
                    </div>
                </div>
            </Content>
            <ButtonGroup>
                {hasError && (
                    <Button
                        variant='secondary'
                        onPress={() => {
                            void query.refetch();
                        }}
                    >
                        {t('dataset.mediaDetails.retry')}
                    </Button>
                )}
                <Button variant='secondary' onPress={onClose}>
                    {t('common.actions.close')}
                </Button>
            </ButtonGroup>
        </Dialog>
    );
};
