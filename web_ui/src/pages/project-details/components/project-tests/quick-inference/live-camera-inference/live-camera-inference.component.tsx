// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { useState } from 'react';

import { Button, Flex, Grid, Loading, minmax, View } from '@geti/ui';
import { clsx } from 'clsx';
import { v4 as uuid } from 'uuid';

import { Label } from '../../../../../../core/labels/label.interface';
import { fetchMediaAndConvertToFile } from '../../../../../../webworkers/utils';
import { useTaskLabels } from '../../../../../annotator/annotation/annotation-filter/use-task-labels.hook';
import { CaptureButtonAnimation } from '../../../../../camera-page/components/action-buttons/capture-button-animation.component';
import { CameraView } from '../../../../../camera-page/components/camera/camera-view.component';
import { PermissionError } from '../../../../../camera-page/components/camera/permissions-error.component';
import { DeviceSettings } from '../../../../../camera-page/components/sidebar/device-settings.component';
import { ToggleSidebarButton } from '../../../../../camera-page/components/sidebar/toggle-sidebar-button.component';
import {
    DeviceSettingsProvider,
    useDeviceSettings,
} from '../../../../../camera-page/providers/device-settings-provider.component';
import { hasPermissionsDenied, isPermissionPending } from '../../../../../camera-page/util';
import { HeaderOptions } from '../header-options.component';
import { ImageSection } from '../image-section.component';
import { useQuickInference } from '../quick-inference-provider.component';
import { SecondaryToolbar } from '../secondary-toolbar.component';
import { useIsExplanationEnabled } from '../use-is-explanation-enabled.hook';

import styles from './live-camera-interface.module.scss';

interface LiveCameraInferenceLayoutProps {
    shouldShowExplanation: boolean;
    labels: Label[];
}

const Sidebar = ({ isInferencedImageVisible }: { isInferencedImageVisible: boolean }) => {
    const [isOpen, setIsOpen] = useState(true);

    return (
        <Flex direction={'column'} height={'100%'} minHeight={0}>
            <View
                flex={1}
                minHeight={0}
                UNSAFE_className={clsx({ [styles.disabled]: isInferencedImageVisible })}
                padding={'size-250'}
                overflow={'hidden auto'}
                isHidden={!isOpen}
            >
                <DeviceSettings />
            </View>
            <ToggleSidebarButton
                isOpen={isOpen}
                onIsOpenChange={() => setIsOpen((prev) => !prev)}
                flex={isOpen ? undefined : 1}
            />
        </Flex>
    );
};

const InferencedImage = () => {
    const { isLoading } = useQuickInference();

    return (
        <View position={'relative'} height={'100%'} width={'100%'}>
            <ImageSection />
            {isLoading && <Loading mode='overlay' />}
        </View>
    );
};

const CAMERA_ANIMATION_DELAY = 500;

const LiveCameraInferenceLayout = ({ shouldShowExplanation, labels }: LiveCameraInferenceLayoutProps) => {
    const { webcamRef } = useDeviceSettings();
    const { handleUploadImage } = useQuickInference();
    const { image, onResetImage } = useQuickInference();
    const isInferencedImageVisible = image !== undefined;

    const handleTakePhoto = async () => {
        const screenshotUrl = webcamRef.current?.getScreenshot();

        if (screenshotUrl == null) {
            return;
        }

        const screenshot = await fetchMediaAndConvertToFile(uuid(), screenshotUrl);

        if (screenshot === undefined) {
            return;
        }

        // Note: the goal of this timeout is to ensure that camera animation finishes first and then we show predictions
        setTimeout(() => {
            handleUploadImage([screenshot]);
        }, CAMERA_ANIMATION_DELAY);
    };

    return (
        <View
            height={'100%'}
            backgroundColor={'gray-50'}
            borderColor={'gray-50'}
            borderRadius={'regular'}
            borderWidth={'thin'}
        >
            <Grid
                areas={['toolbar toolbar', 'camera sidebar', 'button sidebar']}
                columns={['1fr', 'max-content']}
                rows={['max-content', minmax('size-2400', '1fr'), 'size-1000']}
                gap={'size-100'}
                height={'100%'}
                width={'100%'}
                UNSAFE_className={styles.layout}
            >
                <View gridArea={'toolbar'} UNSAFE_className={clsx({ [styles.disabled]: !isInferencedImageVisible })}>
                    <SecondaryToolbar
                        labels={labels}
                        shouldShowExplanation={shouldShowExplanation}
                        isUploadAllowed={false}
                    />
                </View>
                <View gridArea={'camera'}>
                    <Flex height={'100%'} width={'100%'} justifyContent={'center'} alignItems={'center'}>
                        <View isHidden={!isInferencedImageVisible} height={'100%'}>
                            <InferencedImage />
                        </View>
                        <View isHidden={isInferencedImageVisible} height={'100%'}>
                            <CameraView className={styles.cameraPreview} />
                        </View>
                    </Flex>
                </View>
                <View gridArea={'button'}>
                    <Flex height={'100%'} width={'100%'} justifyContent={'center'} alignItems={'center'}>
                        {isInferencedImageVisible ? (
                            <Button variant='primary' onPress={onResetImage}>
                                Take next shot
                            </Button>
                        ) : (
                            <CaptureButtonAnimation videoTag={webcamRef.current?.video} onPress={handleTakePhoto} />
                        )}
                    </Flex>
                </View>
                <View gridArea={'sidebar'} backgroundColor={'gray-200'}>
                    <Sidebar isInferencedImageVisible={isInferencedImageVisible} />
                </View>
            </Grid>
        </View>
    );
};

const LiveCameraInferenceContent = () => {
    const { imageWasUploaded } = useQuickInference();
    const labels = useTaskLabels();
    const shouldShowExplanation = useIsExplanationEnabled(imageWasUploaded);
    const { userPermissions } = useDeviceSettings();

    if (isPermissionPending(userPermissions)) {
        return <Loading aria-label='permissions pending' />;
    }

    if (hasPermissionsDenied(userPermissions)) {
        return <PermissionError />;
    }

    return (
        <Flex direction={'column'} height={'100%'}>
            <HeaderOptions
                title={`Live camera inference`}
                fullscreenComponent={
                    <LiveCameraInferenceLayout shouldShowExplanation={shouldShowExplanation} labels={labels} />
                }
            />
            <View flex={1} minHeight={0}>
                <LiveCameraInferenceLayout shouldShowExplanation={shouldShowExplanation} labels={labels} />
            </View>
        </Flex>
    );
};

export const LiveCameraInference = () => {
    return (
        <DeviceSettingsProvider>
            <LiveCameraInferenceContent />
        </DeviceSettingsProvider>
    );
};
