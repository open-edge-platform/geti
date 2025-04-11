// INTEL CONFIDENTIAL
//
// Copyright (C) 2022 Intel Corporation
//
// This software and the related documents are Intel copyrighted materials, and your use of them is governed by
// the express license under which they were provided to you ("License"). Unless the License provides otherwise,
// you may not use, modify, copy, publish, distribute, disclose or transmit this software or the related documents
// without Intel's prior written permission.
//
// This software and the related documents are provided as is, with no express or implied warranties,
// other than those that are expressly stated in the License.

import { useMemo } from 'react';

import { Content, Dialog, DialogContainer, Divider, Heading, View } from '@adobe/react-spectrum';
import { OverlayTriggerState } from '@react-stately/overlays';

import { DATASET_IMPORT_STATUSES } from '../../../../../core/datasets/dataset.enum';
import { isAnomalyDomain } from '../../../../../core/projects/domains';
import { useDatasetImportToExistingProject } from '../../../../../providers/dataset-import-to-existing-project-provider/dataset-import-to-existing-project-provider.component';
import { matchStatus } from '../../../../../providers/dataset-import-to-existing-project-provider/utils';
import { DatasetImportDnd } from '../../../../../shared/components/dataset-import-dnd/dataset-import-dnd.component';
import { DatasetImportProgress } from '../../../../../shared/components/dataset-import-progress/dataset-import-progress.component';
import { useProject } from '../../../providers/project-provider/project-provider.component';
import { DatasetImportToExistingProjectDialogButtons } from './dataset-import-to-existing-project-dialog-buttons.component';
import { DatasetImportToExistingProjectMapLabels } from './dataset-import-to-existing-project-map-labels.component';

interface DatasetImportToExistingProjectDialogProps {
    datasetImportDialogState: OverlayTriggerState;
    datasetImportDeleteDialogState: OverlayTriggerState;
}

export const DatasetImportToExistingProjectDialog = ({
    datasetImportDialogState,
    datasetImportDeleteDialogState,
}: DatasetImportToExistingProjectDialogProps) => {
    const { project } = useProject();
    const isAnomaly = project.domains.some(isAnomalyDomain);

    const { setActiveDatasetImportId, activeDatasetImport, prepareDataset, importDatasetJob } =
        useDatasetImportToExistingProject();

    const showProgress = useMemo<boolean>(() => {
        return matchStatus(activeDatasetImport, [
            DATASET_IMPORT_STATUSES.UPLOADING,
            DATASET_IMPORT_STATUSES.PREPARING,
            DATASET_IMPORT_STATUSES.IMPORTING_ERROR,
            DATASET_IMPORT_STATUSES.PREPARING_ERROR,
        ]);
    }, [activeDatasetImport]);

    const showMapLabels = useMemo<boolean>(() => {
        return matchStatus(activeDatasetImport, [
            DATASET_IMPORT_STATUSES.READY,
            DATASET_IMPORT_STATUSES.LABELS_MAPPING_TO_EXISTING_PROJECT,
        ]);
    }, [activeDatasetImport]);

    const dialogDismiss = (): void => {
        datasetImportDialogState.close();
        setActiveDatasetImportId(undefined);
    };

    return (
        <DialogContainer onDismiss={dialogDismiss}>
            {datasetImportDialogState.isOpen && (
                <Dialog aria-label='import-dataset-dialog' width={800}>
                    <Heading>Import dataset</Heading>
                    <Divider />
                    <Content>
                        <View backgroundColor={'gray-50'} minHeight={'size-4600'}>
                            {!activeDatasetImport && (
                                <DatasetImportDnd
                                    setUploadItem={prepareDataset}
                                    setActiveUploadId={setActiveDatasetImportId}
                                    isAnomaly={isAnomaly}
                                    background={false}
                                    paddingX='size-250'
                                    paddingY='size-1000'
                                />
                            )}
                            {activeDatasetImport !== undefined && (
                                <>
                                    {showProgress && (
                                        <View paddingX='size-250' paddingY='size-1000'>
                                            <DatasetImportProgress progressItem={activeDatasetImport} />
                                        </View>
                                    )}
                                    {showMapLabels && (
                                        <View padding='size-250'>
                                            <DatasetImportToExistingProjectMapLabels
                                                projectLabels={project.labels}
                                                activeDatasetImport={activeDatasetImport}
                                            />
                                        </View>
                                    )}
                                </>
                            )}
                        </View>
                    </Content>
                    <DatasetImportToExistingProjectDialogButtons
                        onDialogDismiss={dialogDismiss}
                        datasetImportItem={activeDatasetImport}
                        deletionDialogTriggerState={datasetImportDeleteDialogState}
                        onPrimaryAction={() => {
                            if (!activeDatasetImport) return;

                            importDatasetJob(activeDatasetImport.id);
                        }}
                    />
                </Dialog>
            )}
        </DialogContainer>
    );
};
