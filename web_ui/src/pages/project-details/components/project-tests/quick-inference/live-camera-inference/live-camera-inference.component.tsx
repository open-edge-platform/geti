// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { Button, Flex, Grid, Loading, minmax, View } from '@geti/ui';
import axios from 'axios';
import { v4 as uuid } from 'uuid';

import { Label } from '../../../../../../core/labels/label.interface';
import { useTaskLabels } from '../../../../../annotator/annotation/annotation-filter/use-task-labels.hook';
import { CaptureButtonAnimation } from '../../../../../camera-page/components/action-buttons/capture-button-animation.component';
import { CameraView } from '../../../../../camera-page/components/camera/camera-view.component';
import { DeviceSettings } from '../../../../../camera-page/components/sidebar/device-settings.component';
import {
    DeviceSettingsProvider,
    useDeviceSettings,
} from '../../../../../camera-page/providers/device-settings-provider.component';
import { HeaderOptions } from '../header-options.component';
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

interface LiveCameraInferenceContentProps {
    shouldShowExplanation: boolean;
    labels: Label[];
}

const Sidebar = () => {
    return <DeviceSettings />;
};

const InferencedImage = () => {
    const { isLoading } = useQuickInference();

    return (
        <View position={'relative'} height={'100%'} width={'100%'}>
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

const LiveCameraInferenceContent = ({ shouldShowExplanation, labels }: LiveCameraInferenceContentProps) => {
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
                columns={['1fr', 'size-3400']}
                rows={['max-content', minmax('size-3400', '1fr'), 'size-1000']}
                height={'100%'}
                width={'100%'}
            >
                <View gridArea={'toolbar'}>
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
                <View
                    gridArea={'sidebar'}
                    backgroundColor={'gray-200'}
                    padding={'size-250'}
                    UNSAFE_style={{ boxSizing: 'border-box' }}
                    overflow={'hidden auto'}
                >
                    <Sidebar />
                </View>
            </Grid>
        </View>
    );
};

export const LiveCameraInference = () => {
    const { imageWasUploaded } = useQuickInference();
    const labels = useTaskLabels();
    const shouldShowExplanation = useIsExplanationEnabled(imageWasUploaded);

    return (
        <DeviceSettingsProvider>
            <Flex direction={'column'}>
                <HeaderOptions
                    title={`Live camera inference`}
                    fullscreenComponent={
                        <LiveCameraInferenceContent shouldShowExplanation={shouldShowExplanation} labels={labels} />
                    }
                />
                <View flex={1}>
                    <LiveCameraInferenceContent shouldShowExplanation={shouldShowExplanation} labels={labels} />
                </View>
            </Flex>
        </DeviceSettingsProvider>
    );
};
