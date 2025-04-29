// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { ButtonGroup, Content, Dialog, DialogContainer, Divider, Flex, Heading, View } from '@adobe/react-spectrum';
import { useNavigate } from 'react-router-dom';

import { isAnomalyDomain } from '../../../../../../core/projects/domains';
import { paths } from '../../../../../../core/services/routes';
import { UploadMedia } from '../../../../../../providers/media-upload-provider/media-upload.interface';
import { Button } from '../../../../../../shared/components/button/button.component';
import { UploadMediaButton } from '../../../../../../shared/components/upload-media/upload-media-button/upload-media-button.component';
import { useDatasetIdentifier } from '../../../../../annotator/hooks/use-dataset-identifier.hook';
import { useProject } from '../../../../providers/project-provider/project-provider.component';
import { UploadStatusDialogContent } from './upload-status-dialog-content.component';
import { UploadStatusDialogTime } from './upload-status-dialog-time.component';

import classes from './upload-status-dialog.module.scss';

interface UploadStatusDialogProps {
    isOpen: boolean;
    isUploadInProgress: boolean;
    onClose: () => void;
    abortMediaUploads: () => void;
    onUploadMedia: (uploads: UploadMedia) => Promise<void>;
}

export const UploadStatusDialog = ({
    isOpen,
    onClose,
    onUploadMedia,
    abortMediaUploads,
    isUploadInProgress,
}: UploadStatusDialogProps): JSX.Element => {
    const navigate = useNavigate();
    const datasetIdentifier = useDatasetIdentifier();
    const { isSingleDomainProject } = useProject();

    return (
        <DialogContainer onDismiss={onClose}>
            {isOpen && (
                <Dialog>
                    <Heading>{isUploadInProgress ? 'Uploading' : 'Uploaded'}</Heading>
                    <Divider />

                    <Content>
                        <UploadStatusDialogContent />
                        {isUploadInProgress && <UploadStatusDialogTime />}
                    </Content>

                    <ButtonGroup UNSAFE_style={{ paddingLeft: 0 }}>
                        <Flex
                            width='100%'
                            alignItems='center'
                            justifyContent={isUploadInProgress ? 'space-between' : 'end'}
                        >
                            <Button
                                marginEnd={'size-125'}
                                type='reset'
                                variant={'secondary'}
                                UNSAFE_className={classes.cancelAllButton}
                                isHidden={!isUploadInProgress}
                                onPress={() => {
                                    abortMediaUploads();
                                    onClose();
                                }}
                            >
                                Cancel all pending
                            </Button>
                            <View
                                paddingTop={`${isUploadInProgress ? 'size-300' : 0}`}
                                UNSAFE_className={classes.buttonGroup}
                            >
                                {!isSingleDomainProject(isAnomalyDomain) && (
                                    <UploadMediaButton
                                        id='upload-more-media-action-menu'
                                        title='Upload more'
                                        variant='secondary'
                                        ariaLabel='upload more'
                                        onCameraSelected={() => {
                                            navigate(paths.project.dataset.camera(datasetIdentifier));
                                        }}
                                        uploadCallback={(files: File[]) => {
                                            onUploadMedia({ datasetIdentifier, files });
                                        }}
                                    />
                                )}
                                <Button variant={'secondary'} marginStart='size-75' onPress={onClose}>
                                    Hide
                                </Button>
                            </View>
                        </Flex>
                    </ButtonGroup>
                </Dialog>
            )}
        </DialogContainer>
    );
};
