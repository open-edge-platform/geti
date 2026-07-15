// Copyright (C) 2025-2026 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

import { ComponentProps } from 'react';

import { BulkLabelsAssignmentDialog } from '../bulk-labels-assignment/bulk-labels-assignment-dialog.component';
import { useUploadFiles } from '../use-upload-files';
import { AddMediaButton } from './add-media-button/add-media-button.component';

type MediaUploadProps = {
    uploadMediaVariant?: ComponentProps<typeof AddMediaButton>['variant'];
};

export const MediaUpload = ({ uploadMediaVariant }: MediaUploadProps) => {
    const { isClassification, uploadFiles, uploadMediaLoading, clearFilesForLabelAssignment, filesForLabelAssignment } =
        useUploadFiles();

    return (
        <>
            <AddMediaButton onFileUpload={uploadFiles} isDisabled={uploadMediaLoading} variant={uploadMediaVariant} />
            {isClassification && (
                <BulkLabelsAssignmentDialog onClose={clearFilesForLabelAssignment} files={filesForLabelAssignment} />
            )}
        </>
    );
};
