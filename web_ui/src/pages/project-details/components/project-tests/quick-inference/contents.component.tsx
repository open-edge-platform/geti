// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { useEffect } from 'react';

import { Flex, Loading, View } from '@geti/ui';
import { useNavigate } from 'react-router-dom';

import { NoTrainedModels } from '../../../../../assets/images';
import { useModels } from '../../../../../core/models/hooks/use-models.hook';
import { paths } from '../../../../../core/services/routes';
import { EmptyData } from '../../../../../shared/components/empty-data/empty-data.component';
import { MediaDropBoxHeader } from '../../../../../shared/components/media-drop/media-drop-box-header.component';
import { MediaDropBox } from '../../../../../shared/components/media-drop/media-drop-box.component';
import { VALID_IMAGE_TYPES } from '../../../../../shared/media-utils';
import { useDatasetIdentifier } from '../../../../annotator/hooks/use-dataset-identifier.hook';
import { useCameraStorage } from '../../../../camera-page/hooks/use-camera-storage.hook';
import { ImageSection } from './image-section.component';
import { useQuickInference } from './quick-inference-provider.component';
import { WaitingInference } from './waiting-inference.component';

import classes from '../project-tests.module.scss';

interface LoadFileFromLiveInferenceCameraProps {
    onFileLoaded: (files: File[] | FileList) => void;
}

const LoadFileFromLiveInferenceCamera = ({ onFileLoaded }: LoadFileFromLiveInferenceCameraProps) => {
    const { savedFilesQuery, deleteAllItems } = useCameraStorage();
    const [firstFile] = savedFilesQuery.data ?? [];

    useEffect(() => {
        if (firstFile?.isAccepted) {
            deleteAllItems().then(() => onFileLoaded([firstFile.file]));
        }
        // eslint-disable-next-line react-hooks/exhaustive-deps
    }, [firstFile?.isAccepted]);

    return <></>;
};

export const Contents = () => {
    const navigate = useNavigate();
    const datasetIdentifier = useDatasetIdentifier();
    const { useHasActiveModels } = useModels();
    const { hasActiveModels } = useHasActiveModels();

    const { handleUploadImage, imageWasUploaded, isDisabled, isLoading, showWarningCard, dismissWarningCard } =
        useQuickInference();

    if (isDisabled) {
        return (
            <EmptyData
                title={'No trained models'}
                text={'Upload media and annotate to train a new model'}
                beforeText={<NoTrainedModels />}
            />
        );
    }

    const acceptedFormats = VALID_IMAGE_TYPES;
    const isMultipleUpload = false;

    // we don't want to allow user to reupload if inference is running
    // we hide a drop media box if we already have uploaded image
    return (
        // 100% - height of the secondary toolbar
        <Flex direction='column' height={'calc(100% - 48px)'}>
            <View backgroundColor={'gray-50'} width={'100%'} height={'100%'} position='relative' minHeight={0}>
                <MediaDropBox
                    showUploadButton={!imageWasUploaded}
                    isVisible={!imageWasUploaded}
                    onDrop={handleUploadImage}
                    acceptedFormats={acceptedFormats}
                    UNSAFE_className={classes.inferenceMediaDrop}
                    multiple={isMultipleUpload}
                    onCameraSelected={() =>
                        navigate(`${paths.project.dataset.camera(datasetIdentifier)}?isLivePrediction=true`)
                    }
                    dropBoxHeader={<MediaDropBoxHeader formats={acceptedFormats} isMultipleUpload={isMultipleUpload} />}
                    disableUploadButton={!hasActiveModels}
                >
                    {imageWasUploaded && (
                        <>
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
                        </>
                    )}
                </MediaDropBox>
                <LoadFileFromLiveInferenceCamera onFileLoaded={handleUploadImage} />
            </View>
            <WaitingInference isVisible={showWarningCard} dismiss={dismissWarningCard} />
        </Flex>
    );
};
