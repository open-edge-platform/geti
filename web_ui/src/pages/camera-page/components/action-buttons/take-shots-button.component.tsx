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

import { useNavigate } from 'react-router-dom';

import { paths } from '../../../../core/services/routes';
import { Button } from '../../../../shared/components/button/button.component';
import { useCameraParams } from '../../hooks/camera-params.hook';

export const TakeShotsButton = (): JSX.Element => {
    const navigate = useNavigate();
    const { hasDefaultLabel, defaultLabelId, ...datasetIdentifier } = useCameraParams();

    const cameraPagePath = paths.project.dataset.camera(datasetIdentifier);

    return (
        <Button
            variant={'primary'}
            onPress={() =>
                navigate(hasDefaultLabel ? `${cameraPagePath}?defaultLabelId=${defaultLabelId}` : cameraPagePath)
            }
        >
            Take shots
        </Button>
    );
};
