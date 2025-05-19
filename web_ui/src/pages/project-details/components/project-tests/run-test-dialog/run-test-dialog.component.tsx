// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { DialogContainer } from '@geti/ui';

import { RunTestDialogContent } from './run-test-dialog-content.component';
import { RunTestDialogProps } from './run-test-dialog.interface';

export const RunTestDialog = ({
    isOpen,
    modelsGroups,
    handleClose,
    preselectedModel,
}: RunTestDialogProps): JSX.Element => (
    <DialogContainer onDismiss={handleClose}>
        {isOpen && (
            <RunTestDialogContent
                handleClose={handleClose}
                modelsGroups={modelsGroups}
                preselectedModel={preselectedModel}
            />
        )}
    </DialogContainer>
);
