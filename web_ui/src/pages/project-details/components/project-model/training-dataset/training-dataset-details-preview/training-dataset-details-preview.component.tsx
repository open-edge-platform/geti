// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { useState } from 'react';

import { useApplicationServices } from '@geti/core/src/services/application-services-provider.component';
import { Flex, Loading } from '@geti/ui';
import { InfiniteData, UseInfiniteQueryResult } from '@tanstack/react-query';

import { PredictionMode } from '../../../../../../core/annotations/services/prediction-service.interface';
import { Label } from '../../../../../../core/labels/label.interface';
import { isImage } from '../../../../../../core/media/image.interface';
import {
    AdvancedFilterOptions,
    AdvancedFilterSortingOptions,
} from '../../../../../../core/media/media-filter.interface';
import {
    MediaAdvancedFilterResponse,
    MediaItem,
    MediaItemResponse,
} from '../../../../../../core/media/media.interface';
import { isVideoFrame, Video, VideoFrame } from '../../../../../../core/media/video.interface';
import { DatasetIdentifier } from '../../../../../../core/projects/dataset.interface';
import { EditAnnotationsButton } from '../../../../../../shared/components/media-item-annotations-preview/edit-annotations-button/edit-annotations-button.component';
import { ImagePreviewNavigationControls } from '../../../../../../shared/components/media-item-annotations-preview/media-item-annotations-preview-dialog/image-preview-navigation-controls/image-preview-navigation-controls.component';
import { MediaItemAnnotationsPreviewDialog } from '../../../../../../shared/components/media-item-annotations-preview/media-item-annotations-preview-dialog/media-item-annotations-preview-dialog.component';
import { ViewModes } from '../../../../../../shared/components/media-view-modes/utils';
import { useVisibleAnnotations } from '../../../../../../shared/hooks/use-visible-annotations.hook';
import { hasEqualId } from '../../../../../../shared/utils';
import { PreviewCanvasContent } from '../../../../../annotator/components/annotator-preview/preview-canvas-content.component';
import { DatasetList } from '../../../../../annotator/components/sidebar/dataset/dataset-list.component';
import { ANNOTATOR_MODE } from '../../../../../annotator/core/annotation-tool-context.interface';
import { AnnotationToolProvider } from '../../../../../annotator/providers/annotation-tool-provider/annotation-tool-provider.component';
import { useAnnotationsQuery } from '../../../../../annotator/providers/selected-media-item-provider/use-annotations-query.hook';
import { useLoadImageQuery } from '../../../../../annotator/providers/selected-media-item-provider/use-load-image-query.hook';
import { usePredictionsQuery } from '../../../../../annotator/providers/selected-media-item-provider/use-predictions-query.hook';
import { useProject } from '../../../../providers/project-provider/project-provider.component';
import { DetailsPreviewHeader } from '../../../common/details-preview-header/details-preview-header.component';
import { AnnotatorProviders } from '../../../project-test/test-details-preview/annotator-providers.component';
import { TrainingDatasetVideoPlayer } from './training-dataset-video-player.component';

interface TrainingDatasetDetailsPreviewProps {
    selectedMediaItem: MediaItem;
    setSelectedMediaItem: (item: MediaItem | undefined) => void;
    datasetIdentifier: DatasetIdentifier;
    coreLabels: Label[];
    taskId: string;
    revisionId: string;
    searchOptions: AdvancedFilterOptions;
    sortingOptions: AdvancedFilterSortingOptions;
    isActive: boolean;
    modelInformation: string;
    title: string;
    mediaItemsQuery: UseInfiniteQueryResult<InfiniteData<MediaItemResponse | MediaAdvancedFilterResponse>>;
}

export const TrainingDatasetDetailsPreview = ({
    selectedMediaItem,
    setSelectedMediaItem,
    datasetIdentifier,
    coreLabels,
    revisionId,
    searchOptions,
    sortingOptions,
    taskId,
    isActive,
    modelInformation,
    title,
    mediaItemsQuery,
}: TrainingDatasetDetailsPreviewProps): JSX.Element => {
    const { project } = useProject();
    const [mode, setMode] = useState<ANNOTATOR_MODE>(ANNOTATOR_MODE.ACTIVE_LEARNING);
    const [selectedPreviewItem, setSelectedPreviewItem] = useState<MediaItem>(selectedMediaItem);
    const { annotationService } = useApplicationServices();
    const imageQuery = useLoadImageQuery(selectedPreviewItem);
    const selectedTask = project.tasks.find(hasEqualId(taskId)) ?? null;

    const annotationsQuery = useAnnotationsQuery({
        annotationService,
        coreLabels,
        datasetIdentifier,
        mediaItem: selectedPreviewItem,
        annotationId: selectedPreviewItem?.annotationSceneId,
    });

    const close = () => {
        setSelectedMediaItem(undefined);
    };

    const isVisualPrompt = modelInformation.includes('SAM');

    const isPredictionsEnabled = isVisualPrompt || isActive;
    const { predictionsQuery } = usePredictionsQuery({
        mediaItem: selectedPreviewItem,
        datasetIdentifier,
        taskId,
        coreLabels,
        enabled: isPredictionsEnabled,
        predictionId: isVisualPrompt ? PredictionMode.VISUAL_PROMPT : undefined,
    });

    const predictions = useVisibleAnnotations(predictionsQuery.data?.annotations ?? []);
    const explanations = predictionsQuery.data?.maps;

    const annotations = useVisibleAnnotations(annotationsQuery.data ?? []);

    const isLoading = imageQuery.isPending || annotationsQuery.isPending || predictionsQuery.isPending;

    const changeSelectedItem = (mediaItem: MediaItem) => {
        setSelectedMediaItem(mediaItem);

        // We do not want to preview videos as this would trigger video annotations and prediction queries,
        // which don't work
        if (isVideoFrame(mediaItem) || isImage(mediaItem)) {
            setSelectedPreviewItem(mediaItem);
        }
    };

    return (
        <AnnotatorProviders image={imageQuery.data} annotations={annotations} mediaItem={selectedPreviewItem}>
            <AnnotationToolProvider>
                <MediaItemAnnotationsPreviewDialog
                    close={close}
                    additionalButtons={[
                        <EditAnnotationsButton
                            key={'training-dataset-edit-predictions'}
                            datasetIdentifier={datasetIdentifier}
                            mediaItem={selectedPreviewItem}
                        />,
                    ]}
                    title={title}
                    subTitle={modelInformation}
                    selectedPreviewItem={selectedPreviewItem}
                    selectedMediaItem={selectedMediaItem}
                    datasetPreview={
                        <DatasetList
                            selectedMediaItem={selectedMediaItem}
                            selectMediaItem={changeSelectedItem}
                            mediaItemsQuery={mediaItemsQuery}
                            viewMode={ViewModes.SMALL}
                            shouldShowAnnotationIndicator={false}
                            isReadOnly
                        />
                    }
                >
                    <>
                        <DetailsPreviewHeader
                            mode={mode}
                            tasks={project.tasks}
                            selectedTask={selectedTask}
                            setMode={setMode}
                            explanations={explanations}
                            disableActionModes={!isActive && !isVisualPrompt}
                        />
                        <Flex direction='column' height='100%' position='relative' minHeight={0}>
                            {isLoading && isPredictionsEnabled && <Loading mode='overlay' />}

                            <PreviewCanvasContent
                                annotations={annotations}
                                predictions={predictions ?? []}
                                isPredictionMode={mode === ANNOTATOR_MODE.PREDICTION}
                                selectedMediaItem={selectedPreviewItem}
                            />

                            <ImagePreviewNavigationControls
                                selectedMediaItem={selectedMediaItem}
                                changeSelectedItem={changeSelectedItem}
                                mediaItemsQuery={mediaItemsQuery}
                            />
                        </Flex>

                        {selectedMediaItem?.identifier.type === 'video' && (
                            <TrainingDatasetVideoPlayer
                                videoItem={selectedMediaItem as Video}
                                selectedFrame={selectedPreviewItem as VideoFrame}
                                setSelectedFrame={setSelectedPreviewItem}
                                revisionId={revisionId}
                                storageId={datasetIdentifier.datasetId}
                                sortingOptions={sortingOptions}
                                searchOptions={searchOptions}
                            />
                        )}
                    </>
                </MediaItemAnnotationsPreviewDialog>
            </AnnotationToolProvider>
        </AnnotatorProviders>
    );
};
