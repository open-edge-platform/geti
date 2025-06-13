// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { Dispatch, SetStateAction, useCallback, useEffect, useState } from 'react';

import { Flex, Loading } from '@geti/ui';
import { useParams } from 'react-router-dom';

import { Annotation } from '../../../../../core/annotations/annotation.interface';
import { Explanation } from '../../../../../core/annotations/prediction.interface';
import { AdvancedFilterOptions, SearchRuleField } from '../../../../../core/media/media-filter.interface';
import { MediaItem } from '../../../../../core/media/media.interface';
import { DatasetIdentifier } from '../../../../../core/projects/dataset.interface';
import { TASK_TYPE } from '../../../../../core/projects/dtos/task.interface';
import { getDomain } from '../../../../../core/projects/project.interface';
import { SortDirection } from '../../../../../core/shared/query-parameters';
import { useTests } from '../../../../../core/tests/hooks/use-tests.hook';
import { TestImageMediaResult } from '../../../../../core/tests/test-image.interface';
import { TestMediaItem } from '../../../../../core/tests/test-media.interface';
import { Test } from '../../../../../core/tests/tests.interface';
import { useProjectIdentifier } from '../../../../../hooks/use-project-identifier/use-project-identifier';
import { EditAnnotationsButton } from '../../../../../shared/components/media-item-annotations-preview/edit-annotations-button/edit-annotations-button.component';
import { ImagePreviewNavigationControls } from '../../../../../shared/components/media-item-annotations-preview/media-item-annotations-preview-dialog/image-preview-navigation-controls/image-preview-navigation-controls.component';
import { MediaItemAnnotationsPreviewDialog } from '../../../../../shared/components/media-item-annotations-preview/media-item-annotations-preview-dialog/media-item-annotations-preview-dialog.component';
import { ViewModes } from '../../../../../shared/components/media-view-modes/utils';
import { useVisibleAnnotations } from '../../../../../shared/hooks/use-visible-annotations.hook';
import { hasEqualDomain } from '../../../../../shared/utils';
import { PreviewCanvasContent } from '../../../../annotator/components/annotator-preview/preview-canvas-content.component';
import { ANNOTATOR_MODE } from '../../../../annotator/core/annotation-tool-context.interface';
import { AnnotationToolProvider } from '../../../../annotator/providers/annotation-tool-provider/annotation-tool-provider.component';
import { usePrediction } from '../../../../annotator/providers/prediction-provider/prediction-provider.component';
import { sortExplanationsByName } from '../../../../annotator/providers/prediction-provider/utils';
import { useProject } from '../../../providers/project-provider/project-provider.component';
import { DetailsPreviewHeader } from '../../common/details-preview-header/details-preview-header.component';
import { TestMediaItemsList } from '../test-media-items-list.component';
import { AnnotatorProviders } from './annotator-providers.component';
import { useTestResultsQuery } from './use-test-results-query.hook';
import { VideoPlayer } from './video-player.component';

const useTestDatasetIdentifier = (test: Test): DatasetIdentifier => {
    const projectIdentifier = useProjectIdentifier();
    return {
        ...projectIdentifier,
        datasetId: test.datasetsInfo[0].id ?? '',
    };
};

interface TestDetailsPreviewProps {
    test: Test;
    taskType: TASK_TYPE;
    selectedMediaItem: TestMediaItem;
    setSelectedMediaItem: (media: TestMediaItem | undefined) => void;
    modelInformation: string;
    filter: AdvancedFilterOptions;
    sortDir: SortDirection;
}

interface TestDetailsPreviewWrapperProps
    extends Pick<TestDetailsPreviewProps, 'filter' | 'sortDir' | 'modelInformation' | 'taskType'> {
    testName: string;
    modelInformation: string;
    annotations: Annotation[];
    predictions: Annotation[];
    selectedMediaItem: MediaItem;
    selectedTestMediaItem: TestMediaItem;
    setSelectedTestMediaItem: (media: TestMediaItem | undefined) => void;
    isLoading: boolean;
    datasetIdentifier: DatasetIdentifier;
    explanations: Explanation[] | undefined;
    testResult: TestImageMediaResult | undefined;
    setSelectedMediaItem: Dispatch<SetStateAction<MediaItem>>;
}

const TestDetailsPreviewContent = ({
    filter,
    sortDir,
    taskType,
    testName,
    isLoading,
    testResult,
    annotations,
    predictions,
    explanations,
    modelInformation,
    selectedMediaItem,
    datasetIdentifier,
    setSelectedMediaItem,
    selectedTestMediaItem,
    setSelectedTestMediaItem,
}: TestDetailsPreviewWrapperProps): JSX.Element => {
    const { project } = useProject();
    const [mode, setMode] = useState<ANNOTATOR_MODE>(ANNOTATOR_MODE.PREDICTION);
    const isPredictionMode = mode === ANNOTATOR_MODE.PREDICTION;

    const projectIdentifier = useProjectIdentifier();
    const { testId } = useParams<{ testId: string }>();
    const { useMediaItemsOfTestQuery } = useTests();
    const { setSelectedExplanation } = usePrediction();
    const testDomain = getDomain(taskType.toLowerCase() as TASK_TYPE);
    const selectedTask = project.tasks.find(hasEqualDomain(testDomain)) ?? null;

    const testMediaItemsQuery = useMediaItemsOfTestQuery(projectIdentifier, testId ?? '', filter, {
        sortBy: SearchRuleField.Score,
        sortDir: sortDir === SortDirection.ASC ? 'asc' : 'dsc',
    });

    const { isFetching, hasNextPage, fetchNextPage } = testMediaItemsQuery;

    const loadNextMedia = useCallback(async (): Promise<void> => {
        if (!isFetching && hasNextPage) {
            await fetchNextPage();
        }
    }, [isFetching, hasNextPage, fetchNextPage]);

    const selectTestMediaItem = (mediaItem: TestMediaItem): void => {
        setSelectedExplanation(undefined);
        setSelectedTestMediaItem(mediaItem);
    };

    const close = () => {
        setSelectedTestMediaItem(undefined);
    };

    return (
        <MediaItemAnnotationsPreviewDialog
            close={close}
            additionalButtons={[
                <EditAnnotationsButton
                    key={'test-dataset-edit-predictions'}
                    datasetIdentifier={datasetIdentifier}
                    mediaItem={selectedMediaItem}
                />,
            ]}
            title={testName}
            subTitle={modelInformation}
            selectedPreviewItem={selectedMediaItem}
            selectedMediaItem={selectedMediaItem}
            datasetPreview={
                <TestMediaItemsList
                    viewMode={ViewModes.SMALL}
                    loadNextMedia={loadNextMedia}
                    mediaItemsQuery={testMediaItemsQuery}
                    shouldShowAnnotationIndicator={false}
                    selectMediaItem={selectTestMediaItem}
                    selectedMediaItem={selectedMediaItem}
                />
            }
        >
            <>
                <DetailsPreviewHeader
                    mode={mode}
                    tasks={project.tasks}
                    testResult={testResult}
                    explanations={explanations}
                    selectedTask={selectedTask}
                    setMode={setMode}
                />

                <Flex direction='column' height='100%' position='relative' minHeight={0}>
                    {isLoading && <Loading mode='overlay' />}

                    <PreviewCanvasContent
                        annotations={annotations}
                        predictions={predictions}
                        isPredictionMode={isPredictionMode}
                        selectedMediaItem={selectedMediaItem}
                    />

                    <ImagePreviewNavigationControls<TestMediaItem>
                        selectedMediaItem={selectedTestMediaItem}
                        changeSelectedItem={selectTestMediaItem}
                        mediaItemsQuery={testMediaItemsQuery}
                        showFramesSeparately
                    />
                </Flex>

                {selectedTestMediaItem.type === 'video' && (
                    <VideoPlayer
                        testMediaItem={selectedTestMediaItem}
                        selectedMediaItem={selectedMediaItem}
                        setSelectedMediaItem={setSelectedMediaItem}
                    />
                )}
            </>
        </MediaItemAnnotationsPreviewDialog>
    );
};

export const TestDetailsPreview = ({
    test,
    selectedMediaItem: testMediaItem,
    setSelectedMediaItem: setTestMediaItem,
    modelInformation,
    filter,
    sortDir,
    taskType,
}: TestDetailsPreviewProps) => {
    const [selectedMediaItem, setSelectedMediaItem] = useState<MediaItem>(testMediaItem.media);

    const datasetIdentifier = useTestDatasetIdentifier(test);

    const { imageQuery, annotationsQuery, predictionsQuery, testResult } = useTestResultsQuery(
        datasetIdentifier,
        selectedMediaItem,
        testMediaItem,
        test.id
    );

    const isLoading = imageQuery.isPending || annotationsQuery.isPending || predictionsQuery.isPending;

    const annotations = useVisibleAnnotations(annotationsQuery.data ?? []);
    const predictions = useVisibleAnnotations(predictionsQuery.data?.annotations ?? []);
    const explanations = sortExplanationsByName(predictionsQuery.data?.maps);

    useEffect(() => {
        setSelectedMediaItem(testMediaItem.media);
    }, [testMediaItem]);

    return (
        <AnnotatorProviders image={imageQuery.data} annotations={annotations} mediaItem={selectedMediaItem}>
            <AnnotationToolProvider>
                <TestDetailsPreviewContent
                    taskType={taskType}
                    annotations={annotations}
                    predictions={predictions}
                    selectedTestMediaItem={testMediaItem}
                    isLoading={isLoading}
                    datasetIdentifier={datasetIdentifier}
                    selectedMediaItem={selectedMediaItem}
                    setSelectedTestMediaItem={setTestMediaItem}
                    explanations={explanations}
                    testResult={testResult}
                    setSelectedMediaItem={setSelectedMediaItem}
                    testName={test.testName}
                    filter={filter}
                    modelInformation={modelInformation}
                    sortDir={sortDir}
                />
            </AnnotationToolProvider>
        </AnnotatorProviders>
    );
};
