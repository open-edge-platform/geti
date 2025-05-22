// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { Content, Dialog, DialogContainer, Divider, Heading, View } from '@geti/ui';
import { OverlayTriggerState } from '@react-stately/overlays';

import { DatasetImportItem } from '../../../../../core/datasets/dataset.interface';
import { getCurrentJob } from '../../../../../core/datasets/utils';
import { useFeatureFlags } from '../../../../../core/feature-flags/hooks/use-feature-flags.hook';
import { useJobs } from '../../../../../core/jobs/hooks/use-jobs.hook';
import { useDatasetImportToNewProject } from '../../../../../providers/dataset-import-to-new-project-provider/dataset-import-to-new-project-provider.component';
import { useWorkspaceIdentifier } from '../../../../../providers/workspaces-provider/use-workspace-identifier.hook';
import { DatasetImportDeletionDialog } from '../../../../../shared/components/dataset-import-deletion-dialog/dataset-import-deletion-dialog.component';
import { isNonEmptyString, runWhenTruthy } from '../../../../../shared/utils';
import { DatasetImportToNewProjectDialogButtons } from './dataset-import-to-new-project-dialog-buttons.component';
import { DatasetImportToNewProjectDialogContent } from './dataset-import-to-new-project-dialog-content.component';
import { DatasetImportToNewProjectWizard } from './dataset-import-to-new-project-wizard.component';

import classes from './dataset-import-to-new-project.module.scss';

interface DatasetImportToNewProjectDialogProps {
    trigger: OverlayTriggerState;
    deleteDialogTrigger: OverlayTriggerState;
}

export const DatasetImportToNewProjectDialog = ({
    trigger,
    deleteDialogTrigger,
}: DatasetImportToNewProjectDialogProps): JSX.Element => {
    const { FEATURE_FLAG_ANOMALY_REDUCTION } = useFeatureFlags();
    const { organizationId, workspaceId } = useWorkspaceIdentifier();
    const { useCancelJob } = useJobs({ organizationId, workspaceId });

    const {
        isReady,
        importDatasetJob,
        prepareDataset,
        activeDatasetImport,
        patchDatasetImport,
        setActiveDatasetImportId,
        deleteTemporallyDatasetImport,
    } = useDatasetImportToNewProject();

    const dialogDismiss = (): void => {
        trigger.close();
        setActiveDatasetImportId(undefined);
    };

    const abortDatasetImportActionHandler = runWhenTruthy((datasetImportItem: DatasetImportItem) => {
        const currentJobId = getCurrentJob(datasetImportItem);

        isNonEmptyString(currentJobId) && useCancelJob.mutate(currentJobId);
    });

    return (
        <>
            <DialogContainer onDismiss={dialogDismiss}>
                {trigger.isOpen && (
                    <Dialog width={1000} height={800}>
                        <Heading>Create project from a dataset - Import</Heading>
                        <Divider />
                        <Content>
                            <DatasetImportToNewProjectWizard
                                datasetImportItem={activeDatasetImport}
                                patchDatasetImport={patchDatasetImport}
                            />
                            <View UNSAFE_className={classes.modalContent}>
                                <View UNSAFE_className={classes.contentWrapper}>
                                    <DatasetImportToNewProjectDialogContent
                                        datasetImportItem={activeDatasetImport}
                                        prepareDataset={prepareDataset}
                                        patchDatasetImport={patchDatasetImport}
                                        setActiveDatasetImportId={setActiveDatasetImportId}
                                        anomalyRevamp={FEATURE_FLAG_ANOMALY_REDUCTION}
                                    />
                                </View>
                            </View>
                        </Content>

                        <DatasetImportToNewProjectDialogButtons
                            isReady={isReady}
                            patchDatasetImport={patchDatasetImport}
                            onDialogDismiss={dialogDismiss}
                            datasetImportItem={activeDatasetImport}
                            deletionDialogTrigger={deleteDialogTrigger}
                            abortDatasetImportAction={() => abortDatasetImportActionHandler(activeDatasetImport)}
                            deleteTemporallyDatasetImport={deleteTemporallyDatasetImport}
                            onPrimaryAction={() => {
                                if (!activeDatasetImport) return;

                                importDatasetJob(activeDatasetImport.id);
                            }}
                        />
                    </Dialog>
                )}
            </DialogContainer>
            <DatasetImportDeletionDialog
                trigger={deleteDialogTrigger}
                datasetImportItem={activeDatasetImport}
                onPrimaryAction={() => {
                    trigger.close();
                    deleteTemporallyDatasetImport();
                }}
            />
        </>
    );
};
