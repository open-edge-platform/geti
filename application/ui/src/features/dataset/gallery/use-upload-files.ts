// Copyright (C) 2025-2026 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

import { useState } from 'react';

import { useProject } from 'hooks/api/project.hook';

import { isOmeFile, isVideoFile } from '../../../shared/media-file-utils';
import { isClassificationTask } from '../../../shared/task-type-guards';
import { useMediaUpload } from '../api/use-media-upload';
import { useIsUploading } from '../providers/media-upload-context';

export const useUploadFiles = () => {
    const { data: project } = useProject();
    const { uploadMedia } = useMediaUpload();
    const isUploading = useIsUploading();

    const [filesForLabelAssignment, setFilesForLabelAssignment] = useState<File[]>([]);
    const isClassification = isClassificationTask(project.task.task_type);

    const handleFileUpload = async (files: File[]) => {
        if (files.length === 0) {
            return;
        }

        // Videos and OME images are annotated frame by frame (or plane by plane), so they get no label on upload
        if (isClassification && !files.every((file) => isVideoFile(file) || isOmeFile(file))) {
            setFilesForLabelAssignment(files);
        } else {
            await uploadMedia(files);
        }
    };

    const clearFilesForLabelAssignment = () => {
        setFilesForLabelAssignment([]);
    };

    return {
        uploadMedia,
        uploadMediaLoading: isUploading,
        uploadFiles: handleFileUpload,
        isClassification,
        filesForLabelAssignment,
        clearFilesForLabelAssignment,
    };
};
