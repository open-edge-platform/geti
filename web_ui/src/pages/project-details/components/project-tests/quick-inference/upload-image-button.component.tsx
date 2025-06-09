// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { UploadMediaButton } from '../../../../../shared/components/upload-media/upload-media-button/upload-media-button.component';
import { VALID_IMAGE_TYPES } from '../../../../../shared/media-utils';

interface UploadImageButtonProps {
    isDisabled: boolean;
    handleUploadImage: (files: File[] | FileList) => void;
}

export const UploadImageButton = ({ handleUploadImage, isDisabled }: UploadImageButtonProps) => {
    return (
        <UploadMediaButton
            id={'upload-media-button-id'}
            title='Upload'
            multiple={false}
            isDisabled={isDisabled}
            uploadCallback={handleUploadImage}
            acceptedFormats={VALID_IMAGE_TYPES}
            ariaLabel={'upload file'}
        />
    );
};
