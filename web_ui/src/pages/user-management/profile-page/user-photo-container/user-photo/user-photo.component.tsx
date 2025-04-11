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

import { Key } from 'react';

import { Flex, View } from '@adobe/react-spectrum';
import { usePress } from 'react-aria';

import {
    ColorMode,
    QuietActionButton,
} from '../../../../../shared/components/quiet-button/quiet-action-button.component';
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
                <QuietActionButton
                    onPress={handleUploadClick}
                    UNSAFE_className={classes.userPhotoBtn}
                    colorMode={ColorMode.BLUE}
                    isDisabled={isLoading}
                >
                    Change
                </QuietActionButton>
                <QuietActionButton
                    onPress={handleDeleteUserPhoto}
                    UNSAFE_className={classes.userPhotoBtn}
                    colorMode={ColorMode.BLUE}
                    isDisabled={isLoading}
                >
                    Remove
                </QuietActionButton>
            </Flex>
        </Flex>
    );
};
