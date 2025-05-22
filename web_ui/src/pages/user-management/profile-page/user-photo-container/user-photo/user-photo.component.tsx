// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { Key } from 'react';

import { ActionButton, Flex, View } from '@geti/ui';
import { usePress } from 'react-aria';

import { UserPhotoPreview } from './user-photo-preview.component';

import sharedClasses from '../../../../../shared/shared.module.scss';
import classes from './user-photo.module.scss';

interface UserPhotoProps {
    userPhoto: string;
    handleUploadClick: () => void;
    handleDeleteUserPhoto: () => void;
    isLoading: boolean;
}

export const UserPhoto = ({
    userPhoto,
    handleUploadClick,
    handleDeleteUserPhoto,
    isLoading,
}: UserPhotoProps): JSX.Element => {
    const { pressProps } = usePress({ onPress: handleUploadClick });
    const width = 'size-1600';
    const height = 'size-1600';

    return (
        <Flex direction={'column'} width={'max-content'} alignItems={'center'}>
            <View height={height} width={width}>
                <div
                    {...pressProps}
                    className={[classes.userPhotoWrapper, isLoading ? sharedClasses.contentDisabled : ''].join(' ')}
                >
                    <UserPhotoPreview
                        userPhoto={userPhoto}
                        width={width}
                        height={height}
                        // since URL of the user's photo stays the same, key allows us to rerender component
                        key={isLoading as unknown as Key}
                    />
                </div>
            </View>
            <Flex marginTop={'size-200'} justifyContent={'space-between'} alignItems={'center'}>
                <ActionButton
                    isQuiet
                    onPress={handleUploadClick}
                    UNSAFE_className={classes.userPhotoBtn}
                    colorVariant={'blue'}
                    isDisabled={isLoading}
                >
                    Change
                </ActionButton>
                <ActionButton
                    isQuiet
                    onPress={handleDeleteUserPhoto}
                    UNSAFE_className={classes.userPhotoBtn}
                    colorVariant={'blue'}
                    isDisabled={isLoading}
                >
                    Remove
                </ActionButton>
            </Flex>
        </Flex>
    );
};
