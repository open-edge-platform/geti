// Copyright (C) 2026 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

import type { Media } from '@/api/types';
import { formatCompactDuration } from '@/components/media-thumbnail/util';
import { useTranslation } from '@/i18n';
import { Button, ButtonGroup, Content, Dialog, Heading, View } from '@geti-ui/ui';
import { useQuery } from '@tanstack/react-query';
import { useProjectIdentifier } from 'hooks/use-project-identifier.hook';
import { useNumberFormatter } from 'react-aria';

import { annotationsQueryOptions } from '../../../../modules/annotator/shell/api/use-annotations-query';
import { useGetVideoFramesAnnotationsQueryOptions } from '../../../../modules/annotator/video-player/api/use-video-frames-annotations';
import { isVideo } from '../../../../shared/media-item-utils';
import { getThumbnailUrl } from '../../../../shared/media-url.utils';
import { formatBytes } from '../../../../shared/util';
import { getAnnotationCounts } from './media-details.utils';

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
    const framesQueryOptions = useGetVideoFramesAnnotationsQueryOptions({
        mediaId: item.id,
        startFrameIndex: 0,
        endFrameIndex: isVideoItem ? Math.max(0, item.frame_count - 1) : 0,
    });
    const framesQuery = useQuery({
        ...framesQueryOptions,
        enabled: isVideoItem && hasAnnotations,
    });
    const query = isVideoItem ? framesQuery : annotationsQuery;
    const hasError = hasAnnotations && query.isError;
    const videoAnnotationGroups = framesQuery.data?.map((frame) => frame.annotation_data) ?? [];
    const imageAnnotationGroups = annotationsQuery.data ? [annotationsQuery.data] : [];
    const annotationGroups = isVideoItem ? videoAnnotationGroups : imageAnnotationGroups;
    const { annotationCount, labelCount } = getAnnotationCounts(annotationGroups);
    const annotationValue = (value: number) => {
        if (!hasAnnotations) {
            return number.format(0);
        }
        if (query.isPending) {
            return t('common.status.loading');
        }
        if (hasError) {
            return t('common.status.unavailable');
        }
        return number.format(value);
    };
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
        [t('common.labels.annotations'), annotationValue(annotationCount)],
        [t('dataset.mediaDetails.labels'), annotationValue(labelCount)],
    ];

    return (
        <Dialog size={'L'}>
            <Heading>{t('dataset.mediaDetails.title')}</Heading>
            <Content UNSAFE_className={classes.content}>
                <View UNSAFE_className={classes.layout}>
                    <View UNSAFE_className={classes.preview}>
                        <img src={getThumbnailUrl(projectId, item.id)} alt={item.name} />
                    </View>
                    <View UNSAFE_className={classes.details}>
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
                    </View>
                </View>
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
