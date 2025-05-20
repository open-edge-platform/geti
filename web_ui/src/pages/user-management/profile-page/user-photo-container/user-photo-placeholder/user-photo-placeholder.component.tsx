// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { ComponentProps } from 'react';

import { View } from '@geti/ui';
import { isNil } from 'lodash-es';
import { usePress } from 'react-aria';

import { PhotoPlaceholder } from '../../../../../shared/components/photo-placeholder/photo-placeholder.component';
import {
    ColorMode,
    QuietActionButton,
} from '../../../../../shared/components/quiet-button/quiet-action-button.component';

import classes from './user-photo-placeholder.module.scss';

interface UserPhotoPlaceholderProps {
    userName: string;
    email: string;
    handleUploadClick: (() => void) | null;
    width?: ComponentProps<typeof View>['width'];
    height?: ComponentProps<typeof View>['height'];
    disableUpload?: boolean;
}

export const UserPhotoPlaceholder = ({
    userName,
    email,
    handleUploadClick,
    width = 'size-1600',
    height = 'size-1600',
    disableUpload = false,
}: UserPhotoPlaceholderProps): JSX.Element => {
    const isPressable = disableUpload || isNil(handleUploadClick);

    const { pressProps } = usePress({
        onPress: isPressable ? undefined : handleUploadClick,
    });

    return (
        <>
            <div
                {...pressProps}
                id='user-photo-placeholder'
                role={isPressable ? 'button' : ''}
                aria-label={
                    isPressable ? 'Press the photo to choose a different user profile photo' : 'User profile photo'
                }
                className={
                    disableUpload
                        ? classes.userPhotoPlaceholder
                        : handleUploadClick
                          ? classes.userPhotoUploadPlaceholder
                          : ''
                }
            >
                <PhotoPlaceholder name={userName} email={email} width={width} height={height} />
            </div>
            {handleUploadClick && !disableUpload && (
                <QuietActionButton marginTop={'size-200'} onPress={handleUploadClick} colorMode={ColorMode.BLUE}>
                    Upload image
                </QuietActionButton>
            )}
        </>
    );
};
