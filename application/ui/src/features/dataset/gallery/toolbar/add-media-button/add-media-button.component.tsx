// Copyright (C) 2025 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

import { Button, FileTrigger } from '@geti-ui/ui';

import { acceptedExtensions } from '../../utils';

type AddMediaButtonProps = {
    onFileUpload: (files: File[]) => Promise<void>;
    isDisabled?: boolean;
};

export const AddMediaButton = ({ onFileUpload, isDisabled = false }: AddMediaButtonProps) => {
    const handleFileSelect = async (files: FileList | null) => {
        if (files && files.length > 0) {
            await onFileUpload(Array.from(files));
        }
    };

    return (
        <FileTrigger
            data-testid='upload-media-input'
            acceptedFileTypes={[acceptedExtensions]}
            allowsMultiple
            onSelect={handleFileSelect}
        >
            <Button variant={'secondary'} isDisabled={isDisabled}>
                Upload media
            </Button>
        </FileTrigger>
    );
};
