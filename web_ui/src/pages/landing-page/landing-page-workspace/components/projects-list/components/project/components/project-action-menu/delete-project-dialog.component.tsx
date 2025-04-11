// INTEL CONFIDENTIAL
//
// Copyright (C) 2024 Intel Corporation
//
// This software and the related documents are Intel copyrighted materials, and your use of them is governed by
// the express license under which they were provided to you ("License"). Unless the License provides otherwise,
// you may not use, modify, copy, publish, distribute, disclose or transmit this software or the related documents
// without Intel's prior written permission.
//
// This software and the related documents are provided as is, with no express or implied warranties,
// other than those that are expressly stated in the License.

import { AlertDialog } from '@adobe/react-spectrum';

import { ProjectIdentifier } from '../../../../../../../../../core/projects/core.interface';
import { useClearProjectStorage } from '../../../../../../../../../hooks/use-clear-indexeddb-storage/use-clear-indexeddb-storage.hook';

interface DeleteProjectDialogProps {
    projectIdentifier: ProjectIdentifier;
    onDeleteProject: (projectIdentifier: ProjectIdentifier, onSuccess: () => void) => void;
    projectName: string;
}

export const DeleteProjectDialog = ({ onDeleteProject, projectName, projectIdentifier }: DeleteProjectDialogProps) => {
    const { clearProjectStorage } = useClearProjectStorage(projectIdentifier);

    return (
        <AlertDialog
            title='Delete'
            variant='destructive'
            primaryActionLabel='Delete'
            onPrimaryAction={() =>
                clearProjectStorage !== undefined && onDeleteProject(projectIdentifier, clearProjectStorage)
            }
            cancelLabel={'Cancel'}
            isPrimaryActionDisabled={clearProjectStorage === undefined}
        >
            {`Are you sure you want to delete project "${projectName}"?`}
        </AlertDialog>
    );
};
