// Copyright (C) 2025 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

import { Button, FileTrigger } from '@geti-ui/ui';
import { useTranslation } from 'react-i18next';

import { acceptedExtensions } from '../../utils';

type AddMediaButtonProps = {
    onFileUpload: (files: File[]) => Promise<void>;
    isDisabled?: boolean;
};

export const AddMediaButton = ({ onFileUpload, isDisabled = false }: AddMediaButtonProps) => {
    const { t } = useTranslation();

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
            <Button variant={'secondary'} isDisabled={isDisabled} margin={0}>
                {t('dataset.uploadMedia')}
            </Button>
        </FileTrigger>
    );
};
