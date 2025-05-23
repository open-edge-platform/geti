// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { Key, useRef, useState } from 'react';

import { paths } from '@geti/core';
import { Flex, Grid, Loading, useUnwrapDOMRef, View } from '@geti/ui';
import { isEmpty } from 'lodash-es';
import { Navigate } from 'react-router-dom';

import { DOMAIN } from '../../../../core/projects/core.interface';
import { Task } from '../../../../core/projects/task.interface';
import { isKeypointTask } from '../../../../core/projects/utils';
import { useDatasetStatistics } from '../../../../core/statistics/hooks/use-dataset-statistics.hook';
import { useDatasetIdentifier } from '../../../annotator/hooks/use-dataset-identifier.hook';
import { useMedia } from '../../../media/providers/media-provider.component';
import { useProject } from '../../providers/project-provider/project-provider.component';
import { DownloadSvgButton } from '../project-model/model-statistics/download-svg-button.component';
import { ObjectSizeDistributionWrapper } from './object-size-distribution/object-size-distribution-wrapper.component';
import { ProjectAnnotationsImages } from './project-annotations-images/project-annotations-images.component';
import { ProjectAnnotationsMedia } from './project-annotations-media/project-annotations-media.component';
import { ProjectAnnotationsObjects } from './project-annotations-objects/project-annotations-objects.component';
import { ProjectAnnotationsVideos } from './project-annotations-videos/project-annotations-videos.component';
import { TasksList } from './tasks-list/tasks-list.component';

export const ProjectAnnotationsStatistics = (): JSX.Element => {
    const container = useRef(null);
    const unwrappedContainer = useUnwrapDOMRef(container);

    const { organizationId, workspaceId, projectId, datasetId } = useDatasetIdentifier();
    const {
        isTaskChainProject,
        project: { tasks },
    } = useProject();
    const { isLoading: isMediaLoading, media } = useMedia();
    const datasetIdentifier = useDatasetIdentifier();
    const items = tasks.filter(({ domain }: Task) => domain !== DOMAIN.CROP);
    const [selectedTask, setSelectedTask] = useState<string>(items[0].domain);
    const taskId = items.find(({ domain }: Task) => domain === selectedTask)?.id || '';
    const { useGetTaskDatasetStatistics } = useDatasetStatistics();

    const hasNoMediaItems = !isMediaLoading && isEmpty(media);

    const { data: statisticsData, isLoading } = useGetTaskDatasetStatistics({
        organizationId,
        workspaceId,
        projectId,
        datasetId,
        taskId,
        enabled: !hasNoMediaItems,
    });

    if (hasNoMediaItems) {
        return <Navigate to={paths.project.dataset.media(datasetIdentifier)} />;
    }

    const GRID_AREAS_NO_TC = [
        'media images videos',
        'objects objects objects',
        'objects-distribution objects-distribution objects-distribution',
    ];
    const GRID_AREAS_TC = ['task_list . download_graphs', ...GRID_AREAS_NO_TC];
    const GRID_COLUMNS = ['1fr', '1fr', '1fr'];
    const GRID_ROWS_NO_TC = ['17rem', '50rem', '55rem'];
    const GRID_ROWS_TC = ['max-content', ...GRID_ROWS_NO_TC];

    const isKeypoint = tasks.some(isKeypointTask);

    return (
        <Flex
            ref={container}
            height={'100%'}
            direction={'column'}
            position={'relative'}
            id='project-annotations-statistics-id'
        >
            {isLoading ? (
                <Loading />
            ) : statisticsData !== undefined ? (
                <>
                    {!isTaskChainProject && (
                        <DownloadSvgButton
                            marginStart={'auto'}
                            marginBottom={'size-175'}
                            text={'Download all graphs'}
                            fileName={'Project annotations statistics'}
                            container={unwrappedContainer}
                            graphBackgroundColor={'gray-100'}
                        />
                    )}

                    <Grid
                        flex={1}
                        areas={isTaskChainProject ? GRID_AREAS_TC : GRID_AREAS_NO_TC}
                        columns={GRID_COLUMNS}
                        rows={isTaskChainProject ? GRID_ROWS_TC : GRID_ROWS_NO_TC}
                        gap='size-100'
                    >
                        {isTaskChainProject && (
                            <View gridArea={'task_list'}>
                                <TasksList
                                    selectedTask={selectedTask}
                                    setSelectedTask={setSelectedTask}
                                    marginBottom={'size-100'}
                                    items={items}
                                />
                            </View>
                        )}

                        {isTaskChainProject && (
                            <DownloadSvgButton
                                marginStart={'auto'}
                                text={'Download all graphs'}
                                fileName={'Project annotations statistics'}
                                container={unwrappedContainer}
                                graphBackgroundColor={'gray-100'}
                                gridArea={'download_graphs'}
                            />
                        )}

                        <ProjectAnnotationsMedia
                            gridArea='media'
                            images={statisticsData.images}
                            videos={statisticsData.videos}
                        />
                        <ProjectAnnotationsImages
                            gridArea='images'
                            annotatedImages={statisticsData.annotatedImages}
                            images={statisticsData.images}
                        />
                        <ProjectAnnotationsVideos
                            gridArea='videos'
                            annotatedFrames={statisticsData.annotatedFrames}
                            annotatedVideos={statisticsData.annotatedVideos}
                        />
                        <ProjectAnnotationsObjects
                            objectsPerLabel={statisticsData.objectsPerLabel}
                            gridArea='objects'
                        />
                        {/*key - rerender completely ObjectSizeDistributionWrapper component once it gets new value
                         project has at least one label, so we can be sure that it always exists*/}
                        {!isKeypoint && (
                            <ObjectSizeDistributionWrapper
                                gridArea={'objects-distribution'}
                                objectSizeDistribution={statisticsData.objectSizeDistributionPerLabel}
                                key={statisticsData.objectSizeDistributionPerLabel[0].labelId as unknown as Key}
                            />
                        )}
                    </Grid>
                </>
            ) : (
                <></>
            )}
        </Flex>
    );
};
