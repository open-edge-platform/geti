// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { CSSProperties, Key } from 'react';

import { Button } from '@geti/ui';
import { OverlayTriggerState } from 'react-stately';

import { MenuTriggerButton } from '../../../../../shared/components/menu-trigger/menu-trigger-button/menu-trigger-button.component';
import { useProject } from '../../../providers/project-provider/project-provider.component';
import { DatasetTabActions, getDatasetButtonActions } from '../utils';
import { useExportImportDatasetDialogStates } from './export-import-dataset-dialog-provider.component';

interface ExportImportDatasetButtonsProps {
    hasMediaItems: boolean;
}

// Note: we have to overwrite media-drop-box_dropRef styles to make buttons clickable
const BUTTON_STYLES: CSSProperties = {
    pointerEvents: 'all',
};

export const ExportImportDatasetButtons = ({ hasMediaItems }: ExportImportDatasetButtonsProps) => {
    const { isTaskChainProject } = useProject();
    const { datasetImportDialogState, exportDialogState } = useExportImportDatasetDialogStates();
    const showOnlyImportButton = !isTaskChainProject && !hasMediaItems;

    return showOnlyImportButton ? (
        <Button variant='secondary' onPress={datasetImportDialogState.open} UNSAFE_style={BUTTON_STYLES}>
            Import dataset
        </Button>
    ) : !isTaskChainProject ? (
        <ExportImportMenu
            hasMediaItems={hasMediaItems}
            isTaskChainProject={isTaskChainProject}
            datasetImportDialogState={datasetImportDialogState}
            exportDialogState={exportDialogState}
        />
    ) : hasMediaItems ? (
        <Button variant='secondary' onPress={exportDialogState.open} UNSAFE_style={BUTTON_STYLES}>
            Export dataset
        </Button>
    ) : null;
};

interface ExportImportMenuProps {
    hasMediaItems: boolean;
    isTaskChainProject: boolean;
    datasetImportDialogState: OverlayTriggerState;
    exportDialogState: OverlayTriggerState;
}

const ExportImportMenu = ({
    hasMediaItems,
    isTaskChainProject,
    datasetImportDialogState,
    exportDialogState,
}: ExportImportMenuProps) => {
    const items = getDatasetButtonActions(hasMediaItems, isTaskChainProject);

    const handleAction = (item: Key): void => {
        if (item === DatasetTabActions.ImportDataset.toLocaleLowerCase()) {
            datasetImportDialogState.open();
        } else if (item === DatasetTabActions.ExportDataset.toLocaleLowerCase()) {
            exportDialogState.open();
        }
    };

    return (
        <MenuTriggerButton
            ariaLabel='Export or import dataset'
            id='export-import-buttons-id'
            variant='secondary'
            items={items}
            onAction={handleAction}
            title='Export/Import'
        />
    );
};
