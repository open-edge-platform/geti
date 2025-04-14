// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { useRef } from 'react';

import { View } from '@adobe/react-spectrum';
import { AnimatePresence, motion } from 'framer-motion';

import { useUsers } from '../../../../core/users/hook/use-users.hook';
import { useIsSaasEnv } from '../../../../hooks/use-is-saas-env/use-is-saas-env.hook';
import { useOrganizationIdentifier } from '../../../../hooks/use-organization-identifier/use-organization-identifier.hook';
import { NOTIFICATION_TYPE } from '../../../../notification/notification-toast/notification-type.enum';
import { useNotification } from '../../../../notification/notification.component';
import {
    isValidationFailReason,
    mediaExtensionHandler,
    validateImage,
} from '../../../../providers/media-upload-provider/media-upload.validator';
import { ANIMATION_PARAMETERS } from '../../../../shared/animation-parameters/animation-parameters';
import { VALID_IMAGE_TYPES_SINGLE_UPLOAD } from '../../../../shared/media-utils';
import { onValidFileList } from '../../../../shared/utils';
import { isSupportedImageFormat } from '../../../utils';
import { PictureLimits } from './picture-limits.component';
import { UserPhotoPlaceholder } from './user-photo-placeholder/user-photo-placeholder.component';
import { UserPhoto } from './user-photo/user-photo.component';
import { USER_PHOTO_VALIDATION_MESSAGES, USER_PHOTO_VALIDATION_RULES } from './utils';

interface UserPhotoContainerProps {
    userId: string;
    userName: string;
    email: string;
    userPhoto: string | null;
}

export const UserPhotoContainer = ({ userId, userName, userPhoto, email }: UserPhotoContainerProps): JSX.Element => {
    const uploadRef = useRef<HTMLInputElement>(null);
    const { organizationId } = useOrganizationIdentifier();

    const { useUploadUserPhoto, useDeleteUserPhoto } = useUsers();
    const uploadUserPhoto = useUploadUserPhoto();
    const deleteUserPhoto = useDeleteUserPhoto();

    const { addNotification } = useNotification();

    const acceptedFormats = mediaExtensionHandler(VALID_IMAGE_TYPES_SINGLE_UPLOAD);

    const handleUploadPhoto = onValidFileList(async ([file]: File[]) => {
        if (!isSupportedImageFormat(file)) {
            addNotification({
                message: `This feature only supports image files. Supported extensions: ${acceptedFormats}`,
                type: NOTIFICATION_TYPE.ERROR,
            });

            return;
        }

        try {
            await validateImage(file, USER_PHOTO_VALIDATION_RULES, USER_PHOTO_VALIDATION_MESSAGES);

            uploadUserPhoto.mutate({ organizationId, userId, userPhoto: file });
        } catch (error: unknown) {
            if (isValidationFailReason(error)) {
                const errorMessage = error.errors.length === 1 ? error.errors[0] : error.errors.join('\n');

                addNotification({ message: errorMessage, type: NOTIFICATION_TYPE.ERROR });
            }
        }
    });

    const handleDeleteUserPhoto = () => {
        deleteUserPhoto.mutate({ organizationId, userId });
    };

    const handleUploadClick = (): void => {
        uploadRef.current?.click();
    };

    const isSaaS = useIsSaasEnv();
    // TODO: reenable once we support uploading user profile photos
    const allowChangingProfilePhoto = false && isSaaS;

    return (
        <View marginBottom={'size-400'} maxWidth={'size-1600'}>
            <input
                type={'file'}
                aria-label={'Upload user photo'}
                ref={uploadRef}
                onChange={({ target }) => handleUploadPhoto(target.files)}
                accept={acceptedFormats}
                disabled={uploadUserPhoto.isPending}
                hidden
            />
            <AnimatePresence>
                <motion.div variants={ANIMATION_PARAMETERS.FADE_ITEM} initial={'hidden'} animate={'visible'}>
                    {userPhoto && !allowChangingProfilePhoto ? (
                        <UserPhoto
                            userPhoto={userPhoto}
                            handleUploadClick={handleUploadClick}
                            handleDeleteUserPhoto={handleDeleteUserPhoto}
                            isLoading={uploadUserPhoto.isPending || deleteUserPhoto.isPending}
                        />
                    ) : (
                        <UserPhotoPlaceholder
                            userName={userName}
                            email={email}
                            handleUploadClick={handleUploadClick}
                            disableUpload={!allowChangingProfilePhoto}
                        />
                    )}
                    {allowChangingProfilePhoto && <PictureLimits />}
                </motion.div>
            </AnimatePresence>
        </View>
    );
};
