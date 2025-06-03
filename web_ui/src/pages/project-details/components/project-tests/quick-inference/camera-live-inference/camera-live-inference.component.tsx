// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { Button, ButtonGroup, Content, Dialog, DialogContainer, Divider, Grid, Heading, Loading, View } from '@geti/ui';
import axios from 'axios';
import { v4 as uuid } from 'uuid';

import { useTaskLabels } from '../../../../../annotator/annotation/annotation-filter/use-task-labels.hook';
import { CaptureButtonAnimation } from '../../../../../camera-page/components/action-buttons/capture-button-animation.component';
import { CameraView } from '../../../../../camera-page/components/camera/camera-view.component';
import { DeviceSettings } from '../../../../../camera-page/components/sidebar/device-settings.component';
import {
    DeviceSettingsProvider,
    useDeviceSettings,
} from '../../../../../camera-page/providers/device-settings-provider.component';
import { ImageSection } from '../image-section.component';
import { useQuickInference } from '../quick-inference-provider.component';
import { useIsExplanationEnabled } from '../quick-inference.component';
import { SecondaryToolbar } from '../secondary-toolbar.component';

const getBlobFromDataUrl = async (dataUrl: string): Promise<Blob> => {
    const response = await axios.get(dataUrl, {
        responseType: 'blob',
    });

    return response.data;
};

/*
    1) Gets the blob from the source data url
    2) Converts the .webp blob to .jpeg blob if necessary
    3) Creates and returns a new file based on the blob
*/
const fetchMediaAndConvertToFile = async (id: string, dataUrl: string) => {
    const blob = await getBlobFromDataUrl(dataUrl);

    if (blob === undefined) {
        return;
    }

    const fileType = blob.type.split('/').pop();
    const fileName = `${id}.${fileType}`;

    return new File([blob], fileName, { type: blob.type });
};

interface CameraLiveInferenceDialogProps {
    onClose: () => void;
    isOpen: boolean;
}

const Sidebar = () => {
    return <DeviceSettings />;
};

const CameraLiveInference = () => {
    const { webcamRef } = useDeviceSettings();
    const { handleUploadImage } = useQuickInference();

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
        <Grid
            areas={['camera sidebar', 'button sidebar']}
            columns={['1fr', 'size-3400']}
            rows={['1fr', 'size-900']}
            height={'100%'}
            width={'100%'}
        >
            <View gridArea={'camera'} alignSelf={'center'} justifySelf={'center'}>
                <CameraView />
            </View>
            <View gridArea={'button'} justifySelf={'center'}>
                <CaptureButtonAnimation videoTag={webcamRef.current?.video} onPress={handleTakePhoto} />
            </View>
            <View gridArea={'sidebar'} backgroundColor={'gray-200'} padding={'size-250'}>
                <Sidebar />
            </View>
        </Grid>
    );
};

const InferencedImage = () => {
    const { isLoading, imageWasUploaded } = useQuickInference();
    const labels = useTaskLabels();
    const shouldShowExplanation = useIsExplanationEnabled(imageWasUploaded);

    return (
        <View position={'relative'} height={'100%'} width={'100%'}>
            <SecondaryToolbar labels={labels} shouldShowExplanation={shouldShowExplanation} isUploadAllowed={false} />
            <ImageSection />
            {isLoading && (
                <View
                    position='absolute'
                    top={0}
                    bottom={0}
                    left={0}
                    right={0}
                    UNSAFE_style={{ backgroundColor: 'rgba(36 37 40 / 60%)' }}
                >
                    <Loading />
                </View>
            )}
        </View>
    );
};

export const CameraLiveInferenceDialog = ({ onClose, isOpen }: CameraLiveInferenceDialogProps) => {
    const { image, onResetImage } = useQuickInference();
    const isInferencedImageVisible = image !== undefined;

    const handleTakeNext = () => {
        onResetImage();
    };

    const handleClose = () => {
        onClose();
        onResetImage();
    };

    return (
        <DeviceSettingsProvider>
            <DialogContainer type={'fullscreenTakeover'} onDismiss={handleClose}>
                {isOpen && (
                    <Dialog>
                        <Heading>Camera live inference</Heading>
                        <Divider />
                        <Content>
                            <View isHidden={image !== undefined} width={'100%'} height={'100%'}>
                                <CameraLiveInference />
                            </View>
                            {isInferencedImageVisible && <InferencedImage />}
                        </Content>
                        <ButtonGroup>
                            <Button variant='secondary' onPress={handleClose}>
                                Cancel
                            </Button>
                            {isInferencedImageVisible && (
                                <Button variant='primary' onPress={handleTakeNext}>
                                    Take next
                                </Button>
                            )}
                        </ButtonGroup>
                    </Dialog>
                )}
            </DialogContainer>
        </DeviceSettingsProvider>
    );
};
