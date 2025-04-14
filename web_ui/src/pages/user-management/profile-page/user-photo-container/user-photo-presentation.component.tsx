// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

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
