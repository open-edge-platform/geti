// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { Key, useCallback, useMemo } from 'react';

import { Flex } from '@adobe/react-spectrum';
import { useOverlayTriggerState } from '@react-stately/overlays';
import isEmpty from 'lodash/isEmpty';

import { useFeatureFlags } from '../../../../core/feature-flags/hooks/use-feature-flags.hook';
import { Dataset } from '../../../../core/projects/dataset.interface';
import { isKeypointTask } from '../../../../core/projects/utils';
import { useStatus } from '../../../../core/status/hooks/use-status.hook';
import { isBelowTooLowFreeDiskSpace } from '../../../../core/status/hooks/utils';
import { useDataset } from '../../../../providers/dataset-provider/dataset-provider.component';
import { CustomTabItemWithMenu } from '../../../../shared/components/custom-tab-item/custom-tab-item-with-menu.component';
import { CustomTabItem } from '../../../../shared/components/custom-tab-item/custom-tab-item.component';
import { DeleteDialog } from '../../../../shared/components/delete-dialog/delete-dialog.component';
import { EditNameDialog } from '../../../../shared/components/edit-name-dialog/edit-name-dialog.component';
import { useMedia } from '../../../media/providers/media-provider.component';
import { useProject } from '../../providers/project-provider/project-provider.component';
import { ExportDatasetDialog } from './export-dataset/export-dataset-dialog.component';
import { useExportImportDatasetDialogStates } from './export-dataset/export-import-dataset-dialog-provider.component';
import { useSelectedDataset } from './use-selected-dataset/use-selected-dataset.hook';
import { DatasetTabActions, getDatasetTabActions } from './utils';

export interface ProjectDatasetTabActionsProps {
    dataset: Dataset;
}

export const ProjectDatasetTabActions = ({ dataset }: ProjectDatasetTabActionsProps): JSX.Element => {
    const { media } = useMedia();
    const { project, isTaskChainProject } = useProject();
    const { FEATURE_FLAG_KEYPOINT_DETECTION_DATASET_IE } = useFeatureFlags();
    const { handleUpdateDataset: onUpdateDataset, handleDeleteDataset: onDeleteDataset } = useDataset();

    const { data: status } = useStatus();
    const deleteDatasetDialogState = useOverlayTriggerState({});
    const updateDatasetDialogState = useOverlayTriggerState({});
    const { datasetImportDialogState: datasetImportDialogTrigger, exportDialogState } =
        useExportImportDatasetDialogStates();
    const { id: selectedDatasetId, name: selectedDatasetName } = useSelectedDataset();

    const hasMedia = !isEmpty(media);
    const datasetNames = project.datasets.map(({ name }) => name);

    const isTrainingDatasetSelected = dataset.useForTraining;
    const isUploadMediaDisabled = isBelowTooLowFreeDiskSpace(status?.freeSpace ?? 0);
    const isKeypointIeEnabled = project.tasks.some(isKeypointTask) ? FEATURE_FLAG_KEYPOINT_DETECTION_DATASET_IE : true;

    const menuActions = useMemo(
        () => getDatasetTabActions({ hasMediaItems: hasMedia, isTrainingDatasetSelected, isTaskChainProject }),
        [hasMedia, isTaskChainProject, isTrainingDatasetSelected]
    );

    const isSelected = dataset.id === selectedDatasetId;
    const isSelectedAndHasMenu = isSelected && !isEmpty(menuActions);

    const disabledKeys = isUploadMediaDisabled ? [DatasetTabActions.ImportDataset] : [];
    const disableKeypointKeys = !isKeypointIeEnabled
        ? [DatasetTabActions.ExportDataset, DatasetTabActions.ImportDataset]
        : [];

    const onMenuAction = useCallback(
        (tab: Key) => {
            switch (tab) {
                case DatasetTabActions.ImportDataset.toLocaleLowerCase():
                    datasetImportDialogTrigger.open();
                    break;
                case DatasetTabActions.ExportDataset.toLocaleLowerCase():
                    exportDialogState.open();
                    break;
                case DatasetTabActions.DeleteDataset.toLocaleLowerCase():
                    deleteDatasetDialogState.open();
                    break;
                case DatasetTabActions.UpdateDataset.toLocaleLowerCase():
                    updateDatasetDialogState.open();
                    break;
            }
        },
        [datasetImportDialogTrigger, exportDialogState, deleteDatasetDialogState, updateDatasetDialogState]
    );

    return (
        <Flex>
            {isSelectedAndHasMenu ? (
                <CustomTabItemWithMenu
                    name={dataset.name}
                    isMoreIconVisible={isSelectedAndHasMenu}
                    items={menuActions}
                    onAction={onMenuAction}
                    ariaLabel='open dataset menu'
                    id={'dataset-actions'}
                    disabledKeys={[...disabledKeys, ...disableKeypointKeys]}
                />
            ) : (
                <CustomTabItem name={dataset.name} isMoreIconVisible={isSelectedAndHasMenu} />
            )}
            <DeleteDialog
                name={dataset.name}
                title={'dataset'}
                onAction={onDeleteDataset}
                triggerState={deleteDatasetDialogState}
            />
            <EditNameDialog
                triggerState={updateDatasetDialogState}
                onAction={onUpdateDataset}
                defaultName={dataset.name}
                names={datasetNames}
                title={'dataset name'}
            />
            <ExportDatasetDialog triggerState={exportDialogState} datasetName={selectedDatasetName} />
        </Flex>
    );
};
