// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { ButtonGroup, dimensionValue, Flex, Tooltip, TooltipTrigger, useMediaQuery, View } from '@geti/ui';
import { AnimatePresence, motion } from 'framer-motion';
import { isEmpty, negate, noop } from 'lodash-es';
import { useSearchParams } from 'react-router-dom';

import { getAnnotationStateForTask } from '../../../../core/annotations/utils';
import { MEDIA_ANNOTATION_STATUS } from '../../../../core/media/base.interface';
import { MediaItem } from '../../../../core/media/media.interface';
import { isClassificationDomain } from '../../../../core/projects/domains';
import { ANIMATION_PARAMETERS } from '../../../../shared/animation-parameters/animation-parameters';
import { isLargeSizeQuery } from '../../../../theme/queries';
import { useProject } from '../../../project-details/providers/project-provider/project-provider.component';
import { AnnotationToolContext, ANNOTATOR_MODE } from '../../core/annotation-tool-context.interface';
import { useAnnotatorMode } from '../../hooks/use-annotator-mode';
import { useIsSceneBusy } from '../../hooks/use-annotator-scene-interaction-state.hook';
import { useIsPredictionRejected } from '../../providers/annotation-threshold-provider/annotation-threshold-provider.component';
import { useDataset } from '../../providers/dataset-provider/dataset-provider.component';
import { usePrediction } from '../../providers/prediction-provider/prediction-provider.component';
import { useSelectedMediaItem } from '../../providers/selected-media-item-provider/selected-media-item-provider.component';
import { useSelectMediaItemWithSaveConfirmation } from '../../providers/submit-annotations-provider/use-select-media-item-with-save-confirmation.hook';
import { shouldSaveAnnotations } from '../../providers/submit-annotations-provider/utils';
import { useTask } from '../../providers/task-provider/task-provider.component';
import { ToolAnnotationContextProps } from '../../tools/tools.interface';
import useActiveTool from '../../tools/use-active-tool';
import { AcceptPredictionButton } from '../annotator-preview/accept-prediction-button.component';
import { NextMediaItemButton } from './next-media-item-button.component';
import { PreviousMediaItemButton } from './previous-media-item-button.component';
import { SubmitButton } from './submit-button.component';

interface PredictionModeSubmitProps {
    selectedMediaItem: MediaItem | undefined;
    selectMediaItem: (mediaItem: MediaItem) => void;
    annotationToolContext: AnnotationToolContext;
}

const PredictionModeSubmit = ({
    selectMediaItem,
    selectedMediaItem,
    annotationToolContext,
}: PredictionModeSubmitProps) => {
    const { selectedTask } = useTask();
    const { isTaskChainProject } = useProject();
    const isLargeSize = useMediaQuery(isLargeSizeQuery);
    const [searchParams, setSearchParams] = useSearchParams();
    const { predictionAnnotations: predictions } = usePrediction();

    const isClassificationTask = selectedTask && isClassificationDomain(selectedTask.domain);
    const hasSubmitPredictions = isClassificationTask && !isTaskChainProject;
    const marginLeft = isLargeSize ? dimensionValue('size-125') : '0';

    const onSelectActiveLearning = () => {
        searchParams.set('mode', ANNOTATOR_MODE.ACTIVE_LEARNING);
        setSearchParams(searchParams);
    };

    return hasSubmitPredictions ? (
        <SubmitButton
            canSubmit={true}
            newAnnotations={predictions}
            isDisabled={isEmpty(predictions)}
            selectMediaItem={selectMediaItem}
            selectedMediaItem={selectedMediaItem}
            annotationToolContext={annotationToolContext}
            styles={{ marginLeft }}
        />
    ) : (
        <AcceptPredictionButton
            onClose={noop}
            styles={{ marginLeft }}
            isDisabled={isEmpty(predictions)}
            onSuccess={onSelectActiveLearning}
        >
            Use predictions
        </AcceptPredictionButton>
    );
};

export const SecondaryToolbar = ({ annotationToolContext }: ToolAnnotationContextProps): JSX.Element => {
    const activeTool = useActiveTool(annotationToolContext);
    const isLargeSize = useMediaQuery(isLargeSizeQuery);
    const { isDrawing, annotations } = annotationToolContext.scene;

    const isSceneBusy = useIsSceneBusy();
    const { isInActiveMode } = useDataset();
    const { isActiveLearningMode } = useAnnotatorMode();
    const isPredictionRejected = useIsPredictionRejected();
    const { selectedMediaItem, setSelectedMediaItem } = useSelectedMediaItem();

    const acceptedAnnotations = annotations.filter(negate(isPredictionRejected));

    const selectWithSavingConfirmation = useSelectMediaItemWithSaveConfirmation(setSelectedMediaItem);

    const hasLabelsToRevisit =
        getAnnotationStateForTask(selectedMediaItem?.annotationStatePerTask) === MEDIA_ANNOTATION_STATUS.TO_REVISIT;

    const shouldSave = shouldSaveAnnotations(selectedMediaItem?.annotations, acceptedAnnotations) || hasLabelsToRevisit;
    const hasSubmit = isLargeSize || (!isLargeSize && !isDrawing);
    const activeMode = isInActiveMode ? 'Active set' : 'Dataset';
    const isSubmitDisabled = isDrawing || isSceneBusy;

    return (
        <View
            height='size-600'
            paddingX='size-100'
            id='annotator-subheader'
            gridArea='secondaryToolbar'
            backgroundColor='gray-100'
        >
            <Flex
                height='100%'
                alignItems='center'
                justifyContent='space-between'
                UNSAFE_style={{ whiteSpace: 'nowrap' }}
            >
                <AnimatePresence>
                    {activeTool && (
                        <motion.div variants={ANIMATION_PARAMETERS.FADE_ITEM} initial={'hidden'} animate={'visible'}>
                            <activeTool.SecondaryToolbar annotationToolContext={annotationToolContext} />
                        </motion.div>
                    )}
                </AnimatePresence>

                <ButtonGroup marginStart='auto'>
                    {isLargeSize && (
                        <TooltipTrigger placement={'bottom'}>
                            <PreviousMediaItemButton
                                key={'previous-media'}
                                selectMediaItem={selectWithSavingConfirmation}
                                selectedMediaItem={selectedMediaItem}
                            />
                            <Tooltip>{`Go to the previous image from ${activeMode}`}</Tooltip>
                        </TooltipTrigger>
                    )}
                    {isLargeSize && (
                        <TooltipTrigger placement={'bottom'}>
                            <NextMediaItemButton
                                key={'next-media'}
                                selectMediaItem={selectWithSavingConfirmation}
                                selectedMediaItem={selectedMediaItem}
                            />
                            <Tooltip>{`Go to the next image from ${activeMode}`}</Tooltip>
                        </TooltipTrigger>
                    )}
                    {hasSubmit && isActiveLearningMode && (
                        <TooltipTrigger placement={'bottom'}>
                            <SubmitButton
                                key={'submit'}
                                canSubmit={shouldSave}
                                newAnnotations={acceptedAnnotations}
                                isDisabled={isSubmitDisabled}
                                selectMediaItem={setSelectedMediaItem}
                                selectedMediaItem={selectedMediaItem}
                                annotationToolContext={annotationToolContext}
                                styles={{ marginLeft: dimensionValue('size-125') }}
                            />
                            <Tooltip>{`Submit and go to the next unannotated image from ${activeMode}`}</Tooltip>
                        </TooltipTrigger>
                    )}
                    {!isActiveLearningMode && (
                        <TooltipTrigger placement={'bottom'}>
                            <PredictionModeSubmit
                                key={'prediction mode submit'}
                                selectMediaItem={setSelectedMediaItem}
                                selectedMediaItem={selectedMediaItem}
                                annotationToolContext={annotationToolContext}
                            />
                            <Tooltip>{`Merge / Replace with predictions`}</Tooltip>
                        </TooltipTrigger>
                    )}
                </ButtonGroup>
            </Flex>
        </View>
    );
};
