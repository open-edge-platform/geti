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

import { ComponentProps } from 'react';

import { UserPhotoPlaceholder } from './user-photo-placeholder/user-photo-placeholder.component';
import { UserPhotoPreview } from './user-photo/user-photo-preview.component';

interface UserPhotoPresentationProps extends ComponentProps<typeof UserPhotoPlaceholder> {
    userPhoto: string | null;
    email: string;
}

export const UserPhotoPresentation = ({
    userPhoto,
    email,
    userName,
    handleUploadClick,
    width,
    height,
}: UserPhotoPresentationProps): JSX.Element => {
    return userPhoto ? (
        <UserPhotoPreview userPhoto={userPhoto} width={width} height={height} />
    ) : (
        <UserPhotoPlaceholder
            userName={userName}
            handleUploadClick={handleUploadClick}
            email={email}
            width={width}
            height={height}
        />
    );
};
