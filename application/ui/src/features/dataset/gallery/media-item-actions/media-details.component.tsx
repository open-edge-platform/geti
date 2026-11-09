// Copyright (C) 2026 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

import { $api } from '@/api';
import type { Media } from '@/api/types';
import { useTranslation } from '@/i18n';
import { Button, ButtonGroup, Content, Dialog, Heading } from '@geti-ui/ui';
import { useQuery } from '@tanstack/react-query';
import { useProjectIdentifier } from 'hooks/use-project-identifier.hook';
import prettyBytes from 'pretty-bytes';
import { useNumberFormatter } from 'react-aria';

import { annotationsQueryOptions } from '../../../../modules/annotator/shell/api/use-annotations-query';
import { isNonEmptyLabel } from '../../../../shared/labels';
import { getThumbnailUrl, getVideoFrameThumbnailUrl } from '../../../../shared/media-url.utils';

import classes from './media-details.module.scss';

type MediaDetailsProps = {
    item: Media;
    onClose: () => void;
};

export const MediaDetails = ({ item, onClose }: MediaDetailsProps) => {
    const { t, i18n } = useTranslation();
    const projectId = useProjectIdentifier();
    const number = useNumberFormatter({ maximumFractionDigits: 2 });
    const isVideo = item.type === 'video';
    const hasAnnotations = item.annotation_status.has_annotations;
    const annotationsQuery = useQuery({
        ...annotationsQueryOptions(projectId, item),
        enabled: !isVideo && hasAnnotations,
    });
    const framesQuery = $api.useQuery(
        'get',
        '/api/projects/{project_id}/dataset/media/{media_id}/frames',
        { params: { path: { project_id: projectId, media_id: item.id } } },
        { enabled: isVideo && hasAnnotations, retry: false }
    );
    const query = isVideo ? framesQuery : annotationsQuery;
    const hasError = hasAnnotations && query.isError;
    const savedAnnotations = isVideo
        ? framesQuery.data?.flatMap((frame) => frame.annotation_data.annotations)
        : annotationsQuery.data?.annotations;
    const annotations = savedAnnotations?.filter((annotation) => annotation.labels.some(isNonEmptyLabel));
    const annotationCount = annotations?.length ?? 0;
    const labelCount = new Set(
        annotations?.flatMap((annotation) => annotation.labels.filter(isNonEmptyLabel).map((label) => label.id))
    ).size;
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
        [t('dataset.mediaDetails.fileSize'), prettyBytes(item.size, { locale: i18n.language })],
        [t('dataset.mediaDetails.format'), item.format.toUpperCase()],
        [t('dataset.mediaDetails.type'), t(`dataset.mediaDetails.${item.type}`)],
        ...(item.type !== 'image'
            ? [
                  [t('dataset.mediaDetails.frameRate'), `${number.format(item.fps)} FPS`],
                  [t('dataset.mediaDetails.duration'), `${number.format(item.duration)} s`],
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
        <Dialog width='1000px' UNSAFE_className={classes.dialog}>
            <Heading>{t('dataset.mediaDetails.title')}</Heading>
            <Content UNSAFE_className={classes.content}>
                <div className={classes.layout}>
                    <div className={classes.preview}>
                        <img
                            src={
                                item.type === 'video_frame'
                                    ? getVideoFrameThumbnailUrl(projectId, item.id, item.frame_number)
                                    : getThumbnailUrl(projectId, item.id)
                            }
                            alt={item.name}
                        />
                    </div>
                    <div className={classes.details}>
                        <h3 className={classes.name} title={item.name}>
                            {item.name}
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
