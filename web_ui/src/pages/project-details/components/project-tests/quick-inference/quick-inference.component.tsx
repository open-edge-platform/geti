// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { ReactNode, useState } from 'react';

import { Flex, Heading, View } from '@geti/ui';
import { AnimatePresence, motion } from 'framer-motion';

import { NoTrainedModels } from '../../../../../assets/images';
import { useModels } from '../../../../../core/models/hooks/use-models.hook';
import { isKeypointDetection } from '../../../../../core/projects/domains';
import { TUTORIAL_CARD_KEYS } from '../../../../../core/user-settings/dtos/user-settings.interface';
import { useUserGlobalSettings } from '../../../../../core/user-settings/hooks/use-global-settings.hook';
import { getSettingsOfType } from '../../../../../core/user-settings/utils';
import { ANIMATION_PARAMETERS } from '../../../../../shared/animation-parameters/animation-parameters';
import { EmptyData } from '../../../../../shared/components/empty-data/empty-data.component';
import { FullscreenAction } from '../../../../../shared/components/fullscreen-action/fullscreen-action.component';
import { useTaskLabels } from '../../../../annotator/annotation/annotation-filter/use-task-labels.hook';
import { PreviewCanvasSettingsProvider } from '../../../../annotator/providers/preview-canvas-settings-provider/preview-canvas-settings-provider.component';
import { useProject } from '../../../providers/project-provider/project-provider.component';
import { ToggleButtons } from '../../project-models/train-model-dialog/advanced-settings/ui/toggle-buttons/toggle-buttons.component';
import { AnnotatorCanvasProviders } from './annotator-canvas-providers.component';
import { Contents } from './contents.component';
import { HeaderOptions } from './header-options.component';
import { LiveCameraInference } from './live-camera-inference/live-camera-inference.component';
import { LivePredictionNotification } from './live-prediction-notification.component';
import { QuickInferenceProvider, useQuickInference } from './quick-inference-provider.component';
import { SecondaryToolbar } from './secondary-toolbar.component';

import classes from '../project-tests.module.scss';

interface ContentContainerProps {
    imageWasUploaded: boolean;
    shouldShowExplanation: boolean;
}

const ContentContainer = ({ imageWasUploaded, shouldShowExplanation }: ContentContainerProps): JSX.Element => {
    // We want to show a warning card to the user when the inference request is not working
    // We will only do this when the request is not successful yet
    const labels = useTaskLabels();

    return (
        <View
            height={'100%'}
            borderColor={imageWasUploaded ? 'gray-50' : undefined}
            borderRadius={imageWasUploaded ? 'regular' : undefined}
            borderWidth={imageWasUploaded ? 'thin' : undefined}
        >
            <Flex direction={'column'} height={'100%'}>
                {imageWasUploaded && <SecondaryToolbar labels={labels} shouldShowExplanation={shouldShowExplanation} />}
                <Contents />
            </Flex>
        </View>
    );
};

export const useIsExplanationEnabled = (imageWasUploaded: boolean) => {
    const { isTaskChainProject, isSingleDomainProject } = useProject();
    if (imageWasUploaded === false) {
        return false;
    }

    return isTaskChainProject === false && isSingleDomainProject(isKeypointDetection) === false;
};

const LiveFileInference = ({ imageWasUploaded }: { imageWasUploaded: boolean }) => {
    const shouldShowExplanation = useIsExplanationEnabled(imageWasUploaded);

    return (
        <Flex height={'100%'} direction={'column'}>
            {imageWasUploaded && (
                <HeaderOptions
                    title={'Live prediction'}
                    fullscreenComponent={
                        <ContentContainer
                            imageWasUploaded={imageWasUploaded}
                            shouldShowExplanation={shouldShowExplanation}
                        />
                    }
                />
            )}
            <View flex={1} minHeight={0}>
                <ContentContainer imageWasUploaded={imageWasUploaded} shouldShowExplanation={shouldShowExplanation} />
            </View>
        </Flex>
    );
};

type LiveInferenceMode = 'Use file' | 'Use camera';

const QuickInferencePage = (): JSX.Element => {
    const { image, annotations, imageWasUploaded, isDisabled, onResetImage } = useQuickInference();
    const settings = useUserGlobalSettings();
    const isLivePredictionNotificationVisible = getSettingsOfType(settings.config, TUTORIAL_CARD_KEYS)[
        TUTORIAL_CARD_KEYS.LIVE_PREDICTION_NOTIFICATION
    ].isEnabled;
    const [liveInferenceMode, setLiveInferenceMode] = useState<LiveInferenceMode>('Use file');

    const handleInferenceModeChange = (option: LiveInferenceMode) => {
        setLiveInferenceMode(option);
        onResetImage();
    };

    return (
        <AnnotatorCanvasProviders image={image} annotations={annotations}>
            <PreviewCanvasSettingsProvider>
                <Flex height={'100%'} direction={'column'} gap={'size-150'}>
                    <AnimatePresence>
                        {isLivePredictionNotificationVisible && !isDisabled && (
                            <motion.div
                                variants={ANIMATION_PARAMETERS.FADE_ITEM}
                                initial={'hidden'}
                                animate={'visible'}
                                exit={'hidden'}
                            >
                                <LivePredictionNotification settings={settings} />
                            </motion.div>
                        )}
                    </AnimatePresence>

                    <Flex flex={1} width={'100%'} direction={'column'} gap={'size-125'} minHeight={0}>
                        <ToggleButtons
                            options={['Use file', 'Use camera']}
                            selectedOption={liveInferenceMode}
                            onOptionChange={handleInferenceModeChange}
                        />
                        <View flex={1} UNSAFE_className={classes.inferenceContainer}>
                            {liveInferenceMode === 'Use camera' ? (
                                <LiveCameraInference />
                            ) : (
                                <LiveFileInference imageWasUploaded={imageWasUploaded} />
                            )}
                        </View>
                    </Flex>
                </Flex>
            </PreviewCanvasSettingsProvider>
        </AnnotatorCanvasProviders>
    );
};

export const QuickInference = (): JSX.Element => {
    const { useHasActiveModels } = useModels();
    const hasModels = useHasActiveModels();

    if (!hasModels) {
        return (
            <EmptyData
                title={'No trained models'}
                text={'Upload media and annotate to test a model'}
                beforeText={<NoTrainedModels />}
            />
        );
    }

    return (
        <QuickInferenceProvider isDisabled={!hasModels}>
            <QuickInferencePage />
        </QuickInferenceProvider>
    );
};
