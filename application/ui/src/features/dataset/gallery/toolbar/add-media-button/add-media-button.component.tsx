// Copyright (C) 2025 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

import { ActionButton, FileTrigger, Tooltip, TooltipTrigger } from '@geti-ui/ui';
import { Share } from '@geti-ui/ui/icons';

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
            <TooltipTrigger>
                <ActionButton isQuiet aria-label='Upload media' isDisabled={isDisabled}>
                    <Share />
                </ActionButton>
                <Tooltip>Upload media</Tooltip>
            </TooltipTrigger>
        </FileTrigger>
    );
};
