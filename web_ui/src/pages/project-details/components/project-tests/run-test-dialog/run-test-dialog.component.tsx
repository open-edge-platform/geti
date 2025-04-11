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

import { DialogContainer } from '@adobe/react-spectrum';

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
