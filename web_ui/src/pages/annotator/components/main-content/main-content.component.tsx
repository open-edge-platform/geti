// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { useRef } from 'react';

import { Flex, Heading, Loading, Text, useUnwrapDOMRef, View, type DOMRefValue } from '@geti/ui';
import { useErrorHandler } from 'react-error-boundary';

import { EmptyActiveSetIcon } from '../../../../assets/images';
import { Label } from '../../../../core/labels/label.interface';
import { AnnotatorCanvas } from '../../annotator-canvas.component';
import { AnnotatorCanvasSettings } from '../../annotator-settings.component';
import { ToolType } from '../../core/annotation-tool-context.interface';
import { useAnnotatorMode } from '../../hooks/use-annotator-mode';
import { useDataset } from '../../providers/dataset-provider/dataset-provider.component';
import { useIsInActiveMode } from '../../providers/dataset-provider/use-is-in-active-mode.hook';
import { usePrediction } from '../../providers/prediction-provider/prediction-provider.component';
import { useSelectedMediaItem } from '../../providers/selected-media-item-provider/selected-media-item-provider.component';
import { useSubmitAnnotations } from '../../providers/submit-annotations-provider/submit-annotations-provider.component';
import { ModelLoading } from '../../tools/segment-anything-tool/model-loading.component';
import { useSegmentAnything } from '../../tools/segment-anything-tool/segment-anything-state-provider.component';
import { ToolAnnotationContextProps } from '../../tools/tools.interface';
import { TransformZoomAnnotation } from '../../zoom/transform-zoom-annotation.component';
import { LabelsShortcuts } from './labels-shortcuts/labels-shortcuts.component';
import { useSelectFirstMediaItem } from './use-select-first-media-item.hook';

import classes from './main-content.module.scss';

const EmptyDataset = () => {
    const isActiveMode = useIsInActiveMode();

    return (
        <Flex
            alignItems='center'
            justifyContent='center'
            height='100%'
            width='100%'
            direction='column'
            position='absolute'
            top={0}
        >
            <EmptyActiveSetIcon />

            <Heading level={4} UNSAFE_className={classes.activeSetIsEmptyHeader} marginTop='size-150'>
                {isActiveMode ? 'Active set' : 'Dataset'} is empty
            </Heading>

            <Text>Please select a different dataset or upload new media item to annotate more.</Text>
        </Flex>
    );
};

const EmptyMainContent = () => {
    useSelectFirstMediaItem();

    const { mediaItemsQuery } = useDataset();

    const datasetSetIsEmpty =
        !mediaItemsQuery.isPending && !mediaItemsQuery.data?.pages.some((page) => page.media.length !== 0);

    return datasetSetIsEmpty ? (
        <EmptyDataset />
    ) : (
        <Flex alignItems='center' justifyContent='center' height='100%' width='100%' position='absolute' top={0}>
            <Heading level={3} UNSAFE_className={classes.idleHeader}>
                Select a media item to annotate
            </Heading>
        </Flex>
    );
};

const SegmentAnythingLoader = () => {
    const { isLoading, encodingQuery } = useSegmentAnything();

    if (isLoading || encodingQuery.data === undefined) {
        return <ModelLoading isLoadingModel={isLoading} />;
    }

    return <></>;
};

interface MainContentProps extends ToolAnnotationContextProps {
    labels: Label[];
}

export const MainContent = ({ labels, annotationToolContext }: MainContentProps): JSX.Element => {
    const mainContentRef = useRef<DOMRefValue>(null);
    const { isActiveLearningMode } = useAnnotatorMode();
    const unwrappedMainContentRef = useUnwrapDOMRef(mainContentRef);
    const { isExplanationVisible } = usePrediction();
    const { submitAnnotationsMutation } = useSubmitAnnotations();
    const { selectedMediaItem, selectedMediaItemQuery, predictionsQuery } = useSelectedMediaItem();

    const canEditAnnotationLabel = !(predictionsQuery.isFetching || isExplanationVisible);
    const isSaving = submitAnnotationsMutation.isPending;
    const isLoading = selectedMediaItemQuery.isLoading;

    useErrorHandler(selectedMediaItemQuery.error);

    return (
        <View backgroundColor='gray-50' ref={mainContentRef} gridArea='content' overflow='hidden' position='relative'>
            <TransformZoomAnnotation>
                <AnnotatorCanvasSettings>
                    <AnnotatorCanvas
                        selectedMediaItem={selectedMediaItem}
                        annotationToolContext={annotationToolContext}
                        canEditAnnotationLabel={canEditAnnotationLabel}
                    />
                </AnnotatorCanvasSettings>
            </TransformZoomAnnotation>

            {(isLoading || isSaving) && <Loading mode='overlay' />}

            {annotationToolContext.tool === ToolType.SegmentAnythingTool && <SegmentAnythingLoader />}

            {selectedMediaItem === undefined && !isLoading ? <EmptyMainContent /> : <></>}

            <View
                top={0}
                right={0}
                position='absolute'
                paddingTop='size-150'
                UNSAFE_className={classes.labelShortcuts}
                UNSAFE_style={{
                    maxWidth: mainContentRef.current ? unwrappedMainContentRef.current?.offsetWidth : '50%',
                }}
            >
                <LabelsShortcuts
                    labels={labels}
                    annotationToolContext={annotationToolContext}
                    isDisabled={!canEditAnnotationLabel || !isActiveLearningMode}
                />
            </View>
        </View>
    );
};
