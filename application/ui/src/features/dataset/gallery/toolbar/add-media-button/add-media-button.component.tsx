// Copyright (C) 2025 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

import { ActionButton, Button, FileTrigger, Tooltip, TooltipTrigger } from '@geti-ui/ui';
import { Share } from '@geti-ui/ui/icons';

import { acceptedExtensions } from '../../utils';

type AddMediaButtonProps = {
    onFileUpload: (files: File[]) => Promise<void>;
    isDisabled?: boolean;
    variant?: 'icon' | 'text';
};

const LABEL = 'Upload media';

export const AddMediaButton = ({ onFileUpload, isDisabled = false, variant = 'icon' }: AddMediaButtonProps) => {
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
            {variant === 'text' ? (
                <Button variant='primary' isDisabled={isDisabled}>
                    {LABEL}
                </Button>
            ) : (
                <TooltipTrigger>
                    <ActionButton isQuiet aria-label={LABEL} isDisabled={isDisabled}>
                        <Share />
                    </ActionButton>
                    <Tooltip>{LABEL}</Tooltip>
                </TooltipTrigger>
            )}
        </FileTrigger>
    );
};
