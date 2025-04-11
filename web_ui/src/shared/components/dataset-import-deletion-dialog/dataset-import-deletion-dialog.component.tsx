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

import { AlertDialog, DialogContainer } from '@adobe/react-spectrum';
import { OverlayTriggerState } from '@react-stately/overlays';
import isFunction from 'lodash/isFunction';

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
