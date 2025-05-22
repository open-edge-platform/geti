// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { useEffect } from 'react';

import { Flex, Grid, Heading, View } from '@geti/ui';
import { FocusScope } from 'react-aria';

import { hasMaxAllowedAnnotations } from '../../core/annotations/utils';
import { useFeatureFlags } from '../../core/feature-flags/hooks/use-feature-flags.hook';
import { Label } from '../../core/labels/label.interface';
import { isExclusive } from '../../core/labels/utils';
import { isVideo, isVideoFrame } from '../../core/media/video.interface';
import { isKeypointTask } from '../../core/projects/utils';
import {
    FUX_NOTIFICATION_KEYS,
    FUX_SETTINGS_KEYS,
    TUTORIAL_CARD_KEYS,
} from '../../core/user-settings/dtos/user-settings.interface';
import { CoachMark } from '../../shared/components/coach-mark/coach-mark.component';
import { SuccessfullyAutotrainedNotification } from '../../shared/components/coach-mark/fux-notifications/successfully-auto-trained-notification.component';
import { TutorialCardBuilder } from '../../shared/components/tutorial-card/tutorial-card-builder.component';
import { getFuxSetting } from '../../shared/components/tutorials/utils';
import { useTutorialEnablement } from '../../shared/hooks/use-tutorial-enablement.hook';
import { hasEqualId } from '../../shared/utils';
import { ErrorBoundary } from '../errors/error-boundary.component';
import { useProject } from '../project-details/providers/project-provider/project-provider.component';
import { EmptyAnnotationsNotification } from './annotation/annotation-list/annotation-list-thumbnail-grid/empty-annotations-notification.component';
import { BackHome } from './components/back-home/back-home.component';
import { Footer } from './components/footer/footer.component';
import { MainContent } from './components/main-content/main-content.component';
import { NavigationToolbar } from './components/navigation-toolbar/navigation-toolbar.component';
import { PrimaryToolbar } from './components/primary-toolbar/primary-toolbar.component';
import { SecondaryToolbar } from './components/secondary-toolbar/secondary-toolbar.component';
import { Sidebar } from './components/sidebar/sidebar.component';
import { VideoPlayer } from './components/video-player/video-player.component';
import { AnnotationScene } from './core/annotation-scene.interface';
import { useCopyPasteAnnotation } from './hooks/use-copy-paste-annotation/use-copy-paste-annotation.hook';
import { useSelectedAnnotations } from './hooks/use-selected-annotations.hook';
import { useVisibleAnnotations } from './hooks/use-visible-annotations.hook';
import { AutoTrainingCreditsModalFactory } from './notification/auto-training-credits-modal/auto-training-credits-modal.component';
import { AutoTrainingStartedNotification } from './notification/auto-training-started-notification/auto-training-started-notification.component';
import { CreditDeductionNotification } from './notification/credit-deduction-notification/credit-deduction-notification.component';
import { ManualTrainingCreditDeductionNotificationFactory } from './notification/manual-training-credit-deduction-notification/manual-training-credit-deduction-notification.component';
import { ActiveToolProvider } from './providers/annotation-tool-provider/active-tool-provider.component';
import { useAnnotationToolContext } from './providers/annotation-tool-provider/annotation-tool-provider.component';
import { useAnnotator } from './providers/annotator-provider/annotator-provider.component';
import { useROI } from './providers/region-of-interest-provider/region-of-interest-provider.component';
import { useSelectedMediaItem } from './providers/selected-media-item-provider/selected-media-item-provider.component';
import { SelectedMediaItem } from './providers/selected-media-item-provider/selected-media-item.interface';
import { useTask } from './providers/task-provider/task-provider.component';

const GRID_AREAS = [
    'backHome  navigationToolbar  navigationToolbar',
    'primaryToolbar secondaryToolbar  aside',
    'primaryToolbar help  aside',
    'primaryToolbar content  aside',
    'primaryToolbar  videoplayer  aside',
    'primaryToolbar  footer  aside',
];
const GRID_COLUMNS = ['size-600', '1fr', 'auto'];
const GRID_ROWS = ['size-600', 'auto', 'auto', '1fr', 'auto', 'size-400'];

const ErrorFallback = ({ error }: { error: { message: string } }) => {
    return (
        <View backgroundColor='gray-50' gridArea='content' overflow='hidden' position='relative'>
            <Flex alignItems='center' justifyContent='center' height='100%' width='100%' position='absolute' top={0}>
                <Heading level={3} UNSAFE_style={{ color: 'var(--spectrum-global-color-gray-700)' }}>
                    {error.message}
                </Heading>
            </Flex>
        </View>
    );
};

// For now we'll remove any empty labels from a sub task if we're in the "All tasks" view
const useLabelShortcuts = (): Label[] => {
    const { labels: taskLabels, tasks, selectedTask } = useTask();

    if (tasks.length < 2 || selectedTask !== null) {
        return taskLabels.filter((label) => tasks.some((task) => task.labels.some(hasEqualId(label.id))));
    }

    const secondTask = tasks[1];

    return taskLabels.filter((label) => {
        if (!isExclusive(label)) {
            return true;
        }

        return (
            !secondTask.labels.some(hasEqualId(label.id)) &&
            tasks.some((task) => task.labels.some(hasEqualId(label.id)))
        );
    });
};

interface CopyPasteProps {
    labels: Label[];
    scene: AnnotationScene;
    selectedMediaItem: SelectedMediaItem | undefined;
}

const CopyPaste = ({ labels, scene, selectedMediaItem }: CopyPasteProps): JSX.Element => {
    const { image } = useROI();
    const visibleAnnotations = useVisibleAnnotations();
    const selectedAnnotations = useSelectedAnnotations(false);

    useCopyPasteAnnotation({
        scene,
        image,
        taskLabels: labels,
        selectedMediaItem,
        selectedAnnotations,
        hasMultipleAnnotations: visibleAnnotations.length >= 1,
    });

    return <></>;
};

export const AnnotatorLayout = (): JSX.Element => {
    const labels = useLabelShortcuts();
    const { userGlobalSettings, userProjectSettings } = useAnnotator();

    const { project } = useProject();
    const { selectedMediaItem } = useSelectedMediaItem();
    const annotationToolContext = useAnnotationToolContext();
    const { FEATURE_FLAG_CREDIT_SYSTEM } = useFeatureFlags();
    const { isOpen: isAnnotateInteractivelyNotificationEnabled, close } = useTutorialEnablement(
        FUX_NOTIFICATION_KEYS.ANNOTATE_INTERACTIVELY
    );

    const hasPreviouslyAutoTrained = !getFuxSetting(FUX_SETTINGS_KEYS.NEVER_AUTOTRAINED, userGlobalSettings.config);
    const firstAutoTrainedProjectId = getFuxSetting(
        FUX_SETTINGS_KEYS.FIRST_AUTOTRAINED_PROJECT_ID,
        userGlobalSettings.config
    );

    const filteredLabels = project.tasks.some(isKeypointTask) ? [] : labels;

    useEffect(() => {
        if (isAnnotateInteractivelyNotificationEnabled) {
            close();
        }
    });

    return (
        <FocusScope>
            <CopyPaste labels={labels} scene={annotationToolContext.scene} selectedMediaItem={selectedMediaItem} />
            <View backgroundColor='gray-50' overflow='hidden'>
                <Grid
                    gap='size-10'
                    width='100vw'
                    height='100vh'
                    maxWidth='100vw'
                    maxHeight='100vh'
                    rows={GRID_ROWS}
                    areas={GRID_AREAS}
                    columns={GRID_COLUMNS}
                >
                    <BackHome />
                    <Footer />
                    <NavigationToolbar settings={userProjectSettings} />
                    {hasMaxAllowedAnnotations(annotationToolContext.scene.annotations) && (
                        <View gridArea='help'>
                            <TutorialCardBuilder
                                cardKey={TUTORIAL_CARD_KEYS.ANNOTATIONS_COUNT_LIMIT}
                                // The MainContent component has some padding on it, which makes
                                // the margin set in the card builder not necessary
                                styles={{ alignItems: 'center', marginBottom: undefined }}
                            />
                        </View>
                    )}
                    <ActiveToolProvider annotationToolContext={annotationToolContext}>
                        <PrimaryToolbar annotationToolContext={annotationToolContext} />
                        <SecondaryToolbar annotationToolContext={annotationToolContext} />
                        <ErrorBoundary FallbackComponent={ErrorFallback}>
                            <MainContent labels={filteredLabels} annotationToolContext={annotationToolContext} />
                        </ErrorBoundary>
                    </ActiveToolProvider>
                    {selectedMediaItem !== undefined &&
                    (isVideo(selectedMediaItem) || isVideoFrame(selectedMediaItem)) ? (
                        <VideoPlayer />
                    ) : (
                        <></>
                    )}
                    <Sidebar annotationToolContext={annotationToolContext} settings={userProjectSettings} />
                </Grid>
            </View>
            {/* NOTE: we render this notification here (not in the sidebar), because sidebar is hidden in the
                responsive design. */}
            <EmptyAnnotationsNotification />

            <CoachMark
                settingsKey={FUX_NOTIFICATION_KEYS.ANNOTATOR_TOOLS}
                styles={{ position: 'absolute', zIndex: 99999, top: '11rem', left: '6rem' }}
            />

            <AutoTrainingCreditsModalFactory />

            <ManualTrainingCreditDeductionNotificationFactory />

            {FEATURE_FLAG_CREDIT_SYSTEM && <CreditDeductionNotification settings={userGlobalSettings} />}

            {!FEATURE_FLAG_CREDIT_SYSTEM && hasPreviouslyAutoTrained && (
                <AutoTrainingStartedNotification settings={userGlobalSettings} />
            )}

            {firstAutoTrainedProjectId === project.id && <SuccessfullyAutotrainedNotification />}

            <CoachMark
                settingsKey={FUX_NOTIFICATION_KEYS.ANNOTATOR_CHECK_PREDICTIONS}
                styles={{
                    position: 'absolute',
                    top: '50px',
                    zIndex: 99999,
                    right: FEATURE_FLAG_CREDIT_SYSTEM ? '414px' : '375px',
                    width: '355px',
                }}
            />
        </FocusScope>
    );
};
