// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { Key, useRef } from 'react';

import { Button, Flex, FocusableRefValue, Grid, Text, useUnwrapDOMRef } from '@geti/ui';
import Import from '@spectrum-icons/workflow/Import';
import { useNavigate } from 'react-router-dom';

import { paths } from '../../../../../core/services/routes';
import { useUsers } from '../../../../../core/users/hook/use-users.hook';
import { User } from '../../../../../core/users/users.interface';
import { useHandleSignOut } from '../../../../../hooks/use-handle-sign-out/use-handle-sign-out.hook';
import { useOrganizationIdentifier } from '../../../../../hooks/use-organization-identifier/use-organization-identifier.hook';
import { SignOutWarningDialog } from '../../../../../pages/user-management/profile-page/sign-out-warning-dialog.component';
import { UserPhotoPresentation } from '../../../../../pages/user-management/profile-page/user-photo-container/user-photo-presentation.component';
import { getFullNameFromUser } from '../../../../../pages/user-management/users/users-table/utils';
import { useMediaUpload } from '../../../../../providers/media-upload-provider/media-upload-provider.component';
import { HeaderSubmenu } from '../header-submenu/header-submenu.component';

import classes from '../header-actions.module.scss';

enum UserMenuItems {
    USER_INFO = 'User info',
    SIGN_OUT = 'Sign out',
}

interface UserActionsProps {
    isDarkMode: boolean;
}

type UserSignedInProps = Pick<User, 'userPhoto' | 'email'> & { fullName: string };

const UserSignedIn = ({ email, fullName, userPhoto }: UserSignedInProps): JSX.Element => {
    return (
        <Text data-testid={'user-summary-id'} id={'user-summary-id'}>
            <Grid gap={'size-100'} columns={['max-content', '1fr']} alignItems={'start'}>
                <UserPhotoPresentation
                    userPhoto={userPhoto ?? null}
                    userName={fullName}
                    email={email}
                    handleUploadClick={null}
                    width={'size-500'}
                    height={'size-500'}
                />

                <Flex direction={'column'} gap={'size-50'}>
                    {fullName !== email && <Text UNSAFE_className={classes.userSummary}>{fullName}</Text>}
                    <Text UNSAFE_className={classes.email}>{email}</Text>
                </Flex>
            </Grid>
        </Text>
    );
};

export const UserActions = ({ isDarkMode }: UserActionsProps): JSX.Element => {
    const handleSignOut = useHandleSignOut();
    const navigate = useNavigate();
    const { organizationId } = useOrganizationIdentifier();
    const { useActiveUser } = useUsers();
    const { data: activeUser, dataUpdatedAt } = useActiveUser(organizationId);

    const { isUploadInProgress } = useMediaUpload();

    const signOutButtonRef = useRef<FocusableRefValue<HTMLButtonElement>>(null);
    const signOutButtonRefUnwrapped = useUnwrapDOMRef(signOutButtonRef);

    // active user should be fetched before user opens the actions - it's always fetched on page load
    if (activeUser === undefined) {
        return <></>;
    }

    const fullName = getFullNameFromUser(activeUser);

    const ITEMS = [
        {
            children: [
                {
                    text: (
                        <UserSignedIn fullName={fullName} email={activeUser.email} userPhoto={activeUser.userPhoto} />
                    ),
                    id: UserMenuItems.USER_INFO,
                },
            ],
            id: UserMenuItems.USER_INFO,
        },
        {
            children: [
                {
                    text: UserMenuItems.SIGN_OUT,
                    id: UserMenuItems.SIGN_OUT,
                    icon: <Import size={'S'} width={'size-200'} height={'size-200'} />,
                },
            ],
            id: UserMenuItems.SIGN_OUT,
        },
    ];

    const handleMenuAction = (key: Key): void => {
        switch (key) {
            case UserMenuItems.USER_INFO:
                navigate(paths.account.index({ organizationId }));
                break;
            case UserMenuItems.SIGN_OUT:
                isUploadInProgress ? signOutButtonRefUnwrapped.current?.click() : handleSignOut();
                break;
            default:
                return;
        }
    };

    return (
        <>
            <HeaderSubmenu
                ariaLabel={'User actions'}
                items={ITEMS}
                icon={
                    <UserPhotoPresentation
                        // since URL of the user's photo stays the same, key allows us to rerender component
                        key={dataUpdatedAt as unknown as Key}
                        userPhoto={activeUser.userPhoto}
                        userName={fullName}
                        email={activeUser.email}
                        handleUploadClick={null}
                        width={'size-300'}
                        height={'size-300'}
                    />
                }
                onMenuAction={handleMenuAction}
                isDarkMode={isDarkMode}
                buttonClasses={classes.userPhotoBtnBground}
                menuWidth={'size-3000'}
            />

            {isUploadInProgress && (
                <SignOutWarningDialog
                    handleSignOut={handleSignOut}
                    button={
                        <Button variant={'accent'} ref={signOutButtonRef} isHidden>
                            Sign out
                        </Button>
                    }
                />
            )}
        </>
    );
};
