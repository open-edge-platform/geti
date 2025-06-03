// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { ReactNode } from 'react';

import { Flex, Heading, View } from '@geti/ui';
import { AnimatePresence, motion } from 'framer-motion';

import { useModels } from '../../../../../core/models/hooks/use-models.hook';
import { isKeypointDetection } from '../../../../../core/projects/domains';
import { TUTORIAL_CARD_KEYS } from '../../../../../core/user-settings/dtos/user-settings.interface';
import { useUserGlobalSettings } from '../../../../../core/user-settings/hooks/use-global-settings.hook';
import { getSettingsOfType } from '../../../../../core/user-settings/utils';
import { ANIMATION_PARAMETERS } from '../../../../../shared/animation-parameters/animation-parameters';
import { FullscreenAction } from '../../../../../shared/components/fullscreen-action/fullscreen-action.component';
import { useTaskLabels } from '../../../../annotator/annotation/annotation-filter/use-task-labels.hook';
import { PreviewCanvasSettingsProvider } from '../../../../annotator/providers/preview-canvas-settings-provider/preview-canvas-settings-provider.component';
import { useProject } from '../../../providers/project-provider/project-provider.component';
import { AnnotatorCanvasProviders } from './annotator-canvas-providers.component';
import { Contents } from './contents.component';
import { LivePredictionNotification } from './live-prediction-notification.component';
import { QuickInferenceProvider, useQuickInference } from './quick-inference-provider.component';
import { SecondaryToolbar } from './secondary-toolbar.component';

import classes from '../project-tests.module.scss';

interface HeaderOptionsProps {
    fullscreenComponent: ReactNode;
}

const HeaderOptions = ({ fullscreenComponent }: HeaderOptionsProps) => {
    return (
        <Flex alignItems={'center'} justifyContent={'space-between'}>
            <Heading margin={0}>Live prediction</Heading>
            <Flex>
                <FullscreenAction title={'Live prediction'}>{fullscreenComponent}</FullscreenAction>
            </Flex>
        </Flex>
    );
};

interface ContentContainerProps {
    containerHeight?: string;
    imageWasUploaded: boolean;
    shouldShowExplanation: boolean;
}

const ContentContainer = ({
    imageWasUploaded,
    shouldShowExplanation,
    containerHeight = '100%',
}: ContentContainerProps): JSX.Element => {
    // We want to show a warning card to the user when the inference request is not working
    // We will only do this when the request is not successful yet
    const labels = useTaskLabels();

    return (
        <View
            height={containerHeight}
            borderColor={imageWasUploaded ? 'gray-50' : undefined}
            borderRadius={imageWasUploaded ? 'regular' : undefined}
            borderWidth={imageWasUploaded ? 'thin' : undefined}
        >
            {imageWasUploaded && <SecondaryToolbar labels={labels} shouldShowExplanation={shouldShowExplanation} />}
            <Contents />
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

const QuickInferencePage = (): JSX.Element => {
    const { image, annotations, imageWasUploaded, isDisabled } = useQuickInference();
    const settings = useUserGlobalSettings();
    const isLivePredictionNotificationVisible = getSettingsOfType(settings.config, TUTORIAL_CARD_KEYS)[
        TUTORIAL_CARD_KEYS.LIVE_PREDICTION_NOTIFICATION
    ].isEnabled;

    const shouldShowExplanation = useIsExplanationEnabled(imageWasUploaded);

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

                    <Flex
                        // 100% - gap - live prediction notification
                        height={'calc(100% - 50px - size-150)'}
                        flex={1}
                        width={'100%'}
                        direction={'column'}
                        gap={'size-125'}
                        UNSAFE_className={classes.inferenceContainer}
                    >
                        {imageWasUploaded && (
                            <HeaderOptions
                                fullscreenComponent={
                                    <ContentContainer
                                        imageWasUploaded={imageWasUploaded}
                                        shouldShowExplanation={shouldShowExplanation}
                                    />
                                }
                            />
                        )}
                        <ContentContainer
                            // 100% - height of the Header Options
                            containerHeight={imageWasUploaded ? 'calc(100% - 32px - size-100)' : '100%'}
                            imageWasUploaded={imageWasUploaded}
                            shouldShowExplanation={shouldShowExplanation}
                        />
                    </Flex>
                </Flex>
            </PreviewCanvasSettingsProvider>
        </AnnotatorCanvasProviders>
    );
};

export const QuickInference = (): JSX.Element => {
    const { useHasActiveModels } = useModels();
    const hasModels = useHasActiveModels();

    return (
        <QuickInferenceProvider isDisabled={!hasModels}>
            <QuickInferencePage />
        </QuickInferenceProvider>
    );
};
