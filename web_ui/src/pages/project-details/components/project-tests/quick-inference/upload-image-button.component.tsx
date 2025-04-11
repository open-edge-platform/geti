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

import { useNavigate } from 'react-router-dom';

import { paths } from '../../../../../core/services/routes';
import { UploadMediaButton } from '../../../../../shared/components/upload-media/upload-media-button/upload-media-button.component';
import { VALID_IMAGE_TYPES } from '../../../../../shared/media-utils';
import { useDatasetIdentifier } from '../../../../annotator/hooks/use-dataset-identifier.hook';

interface UploadImageButtonProps {
    isDisabled: boolean;
    handleUploadImage: (files: File[] | FileList) => void;
}

export const UploadImageButton = ({ handleUploadImage, isDisabled }: UploadImageButtonProps) => {
    const navigate = useNavigate();
    const datasetIdentifier = useDatasetIdentifier();

    return (
        <UploadMediaButton
            id={'upload-media-button-id'}
            title='Upload'
            multiple={false}
            isDisabled={isDisabled}
            uploadCallback={handleUploadImage}
            acceptedFormats={VALID_IMAGE_TYPES}
            ariaLabel={'upload file'}
            onCameraSelected={() =>
                navigate(`${paths.project.dataset.camera(datasetIdentifier)}?isLivePrediction=true`)
            }
        />
    );
};
