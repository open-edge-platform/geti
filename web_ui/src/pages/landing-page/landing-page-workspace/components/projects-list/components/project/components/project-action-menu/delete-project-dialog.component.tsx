// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { AlertDialog } from '@geti/ui';

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
