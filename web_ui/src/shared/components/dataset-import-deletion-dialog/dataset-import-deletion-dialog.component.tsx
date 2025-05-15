// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { AlertDialog, DialogContainer } from '@adobe/react-spectrum';
import { OverlayTriggerState } from '@react-stately/overlays';
import { isFunction } from 'lodash-es';

import { DatasetImportItem } from '../../../core/datasets/dataset.interface';

interface DatasetImportDeletionDialogProps {
    datasetImportItem: DatasetImportItem | undefined;
    trigger: OverlayTriggerState;
    onPrimaryAction: () => void;
    onDismiss?: () => void;
}

export const DatasetImportDeletionDialog = ({
    datasetImportItem,
    trigger,
    onPrimaryAction,
    onDismiss,
}: DatasetImportDeletionDialogProps): JSX.Element => {
    return (
        <DialogContainer
            onDismiss={() => {
                trigger.close();
                isFunction(onDismiss) && onDismiss();
            }}
        >
            {trigger.isOpen && (
                <AlertDialog
                    title='Delete'
                    variant='destructive'
                    cancelLabel='Cancel'
                    primaryActionLabel='Delete'
                    onPrimaryAction={() => {
                        trigger.close();
                        onPrimaryAction();
                    }}
                >
                    Are you sure you want to delete &quot;{datasetImportItem?.name}&quot;?
                </AlertDialog>
            )}
        </DialogContainer>
    );
};
