// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { useState } from 'react';

import { AlertDialog, DialogContainer, Flex } from '@adobe/react-spectrum';

import { DOMAIN } from '../../../../core/projects/core.interface';
import { isAnomalyDomain } from '../../../../core/projects/domains';
import { MediaUploadActionTypes } from '../../../../providers/media-upload-provider/media-upload-reducer-actions';
import { UploadMedia } from '../../../../providers/media-upload-provider/media-upload.interface';
import { CustomerSupportLink } from '../../../../shared/components/customer-support-link/customer-support-link.component';
import { getIds } from '../../../../shared/utils';
import { useDatasetIdentifier } from '../../../annotator/hooks/use-dataset-identifier.hook';
import { DatasetLoaderManager } from '../../../camera-page/components/loader-managers/dataset-loader-manager.component';
import { useProject } from '../../providers/project-provider/project-provider.component';
import { useDatasetMediaUpload } from '../project-dataset/hooks/dataset-media-upload';
import { useSelectedDataset } from '../project-dataset/use-selected-dataset/use-selected-dataset.hook';
import { AnomalyMediaContent } from './anomaly-media-content.component';
import { MediaContent } from './media-content.component';
import { AnomalyProjectsNotification } from './training-notification/anomaly-projects-notification.component';
import { UploadLabelSelectorDialog } from './upload-label-selector-dialog/upload-label-selector-dialog.component';
import { UploadStatusBar } from './upload-status-bar/upload-status-bar.component';

export const ProjectMedia = (): JSX.Element => {
    const selectedDataset = useSelectedDataset();
    const { isSingleDomainProject, project } = useProject();

    const { mediaUploadState, onUploadMedia, dispatch, abort, reset } = useDatasetMediaUpload();

    const labels = project.labels;

    const isSingleAnomalyProject = isSingleDomainProject(isAnomalyDomain);

    // We should only show the training progress component for anomaly projects
    // and training datasets.
    const showTrainingProcessComponent = isSingleAnomalyProject && selectedDataset.useForTraining;

    const datasetIdentifier = useDatasetIdentifier();
    const [filesForLabelAssignment, setFilesForLabelAssignment] = useState<File[]>([]);
    const labelSelectorDialogActivated = filesForLabelAssignment.length > 0;
    const isSingleDomainClassification = isSingleDomainProject(DOMAIN.CLASSIFICATION);

    const handleUploadMediaCallback = async (uploads: UploadMedia) => {
        if (isSingleDomainClassification) {
            // Allow the user to assign a label to the files before uploading
            setFilesForLabelAssignment(uploads.files);

            return;
        }

        onUploadMedia(uploads);
    };

    return (
        <Flex height='100%'>
            <DatasetLoaderManager mediaUploadState={mediaUploadState} />

            {isSingleDomainClassification && (
                <UploadLabelSelectorDialog
                    tasks={project.tasks}
                    isActivated={labelSelectorDialogActivated}
                    onCancelUpload={abort}
                    onDismiss={() => {
                        setFilesForLabelAssignment([]);
                    }}
                    onSkipAction={() => {
                        const files = filesForLabelAssignment;

                        setFilesForLabelAssignment([]);
                        onUploadMedia({ datasetIdentifier, files });
                    }}
                    onPrimaryAction={(assignedLabels) => {
                        const files = filesForLabelAssignment;
                        const labelIds = getIds(assignedLabels);

                        setFilesForLabelAssignment([]);
                        onUploadMedia({ datasetIdentifier, files, labelIds });
                    }}
                />
            )}

            {isSingleAnomalyProject ? (
                <AnomalyMediaContent
                    labels={labels}
                    onUploadMedia={handleUploadMediaCallback}
                    mediaUploadState={mediaUploadState}
                    dispatch={dispatch}
                />
            ) : (
                <MediaContent
                    mediaUploadState={mediaUploadState}
                    dispatch={dispatch}
                    onUploadMedia={handleUploadMediaCallback}
                />
            )}

            <UploadStatusBar
                reset={reset}
                onUploadMedia={handleUploadMediaCallback}
                mediaUploadState={mediaUploadState}
                abortMediaUploads={abort}
            />

            <DialogContainer
                onDismiss={() =>
                    dispatch({
                        type: MediaUploadActionTypes.SET_INSUFFICIENT_STORAGE,
                        payload: false,
                        datasetId: datasetIdentifier.datasetId,
                    })
                }
            >
                {mediaUploadState.insufficientStorage && (
                    <AlertDialog title='ERROR 507: Insufficient Storage' variant='error' primaryActionLabel='Close'>
                        Your server is running low on disk space. Please contact <CustomerSupportLink /> to find out
                        possible solutions.
                    </AlertDialog>
                )}
            </DialogContainer>

            {showTrainingProcessComponent && <AnomalyProjectsNotification />}
        </Flex>
    );
};
