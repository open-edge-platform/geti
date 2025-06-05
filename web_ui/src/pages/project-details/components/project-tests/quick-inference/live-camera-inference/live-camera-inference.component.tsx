// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { useState } from 'react';

import { ActionButton, Button, Flex, Grid, Loading, minmax, Tooltip, TooltipTrigger, View } from '@geti/ui';
import { ChevronDoubleLeft, ChevronDoubleRight } from '@geti/ui/icons';
import { clsx } from 'clsx';
import { v4 as uuid } from 'uuid';

import { Label } from '../../../../../../core/labels/label.interface';
import { fetchMediaAndConvertToFile } from '../../../../../../webworkers/utils';
import { useTaskLabels } from '../../../../../annotator/annotation/annotation-filter/use-task-labels.hook';
import { CaptureButtonAnimation } from '../../../../../camera-page/components/action-buttons/capture-button-animation.component';
import { CameraView } from '../../../../../camera-page/components/camera/camera-view.component';
import { PermissionError } from '../../../../../camera-page/components/camera/permissions-error.component';
import { DeviceSettings } from '../../../../../camera-page/components/sidebar/device-settings.component';
import {
    DeviceSettingsProvider,
    useDeviceSettings,
} from '../../../../../camera-page/providers/device-settings-provider.component';
import { hasPermissionsDenied, isPermissionPending } from '../../../../../camera-page/util';
import { HeaderOptions } from '../header-options.component';
import { ImageSection } from '../image-section.component';
import { useQuickInference } from '../quick-inference-provider.component';
import { useIsExplanationEnabled } from '../quick-inference.component';
import { SecondaryToolbar } from '../secondary-toolbar.component';

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
            <TooltipTrigger placement={'bottom'}>
                <ActionButton
                    isQuiet
                    onPress={() => setIsOpen((prev) => !prev)}
                    aria-label={'Toggle camera settings'}
                    flex={isOpen ? undefined : 1}
                >
                    {isOpen ? <ChevronDoubleRight size='XS' /> : <ChevronDoubleLeft size='XS' />}
                </ActionButton>
                <Tooltip>{isOpen ? 'Collapse camera settings' : 'Open camera settings'}</Tooltip>
            </TooltipTrigger>
        </Flex>
    );
};

const InferencedImage = () => {
    const { isLoading } = useQuickInference();

    return (
        <View position={'relative'} height={'100%'} width={'100%'}>
            <ImageSection />
            {isLoading && <Loading overlay />}
        </View>
    );
};

const LiveCameraInferenceLayout = ({ shouldShowExplanation, labels }: LiveCameraInferenceLayoutProps) => {
    const { webcamRef } = useDeviceSettings();
    const { handleUploadImage } = useQuickInference();
    const { image, onResetImage } = useQuickInference();
    const isInferencedImageVisible = image !== undefined;

    const handleTakeNext = () => {
        onResetImage();
    };

    const handleTakePhoto = async () => {
        const screenshotUrl = webcamRef.current?.getScreenshot();

        if (screenshotUrl == null) {
            return;
        }

        const screenshot = await fetchMediaAndConvertToFile(uuid(), screenshotUrl);

        if (screenshot === undefined) {
            return;
        }

        setTimeout(() => {
            handleUploadImage([screenshot]);
        }, 500);
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
                        <View isHidden={!isInferencedImageVisible}>
                            <InferencedImage />
                        </View>
                        <View isHidden={isInferencedImageVisible}>
                            <CameraView />
                        </View>
                    </Flex>
                </View>
                <View gridArea={'button'}>
                    <Flex height={'100%'} width={'100%'} justifyContent={'center'} alignItems={'center'}>
                        {isInferencedImageVisible ? (
                            <Button variant='primary' onPress={handleTakeNext}>
                                Take next
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

    const permissionPending = isPermissionPending(userPermissions);

    if (permissionPending) {
        return <Loading aria-label='permissions pending' />;
    }

    const permissionDenied = hasPermissionsDenied(userPermissions);

    if (permissionDenied) {
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
