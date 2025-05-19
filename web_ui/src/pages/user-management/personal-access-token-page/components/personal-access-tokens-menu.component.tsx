// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { Key } from 'react';

import { Flex, Item, Menu, MenuTrigger, Text } from '@geti/ui';
import { useOverlayTriggerState } from '@react-stately/overlays';
import dayjs from 'dayjs';

import { Delete, Edit, MoreMenu } from '../../../../assets/icons';
import { usePersonalAccessToken } from '../../../../core/personal-access-tokens/hooks/use-personal-access-token.hook';
import { PartialPersonalAccessToken } from '../../../../core/personal-access-tokens/personal-access-tokens.interface';
import { useUsers } from '../../../../core/users/hook/use-users.hook';
import { useOrganizationIdentifier } from '../../../../hooks/use-organization-identifier/use-organization-identifier.hook';
import { DeleteDialog } from '../../../../shared/components/delete-dialog/delete-dialog.component';
import { QuietActionButton } from '../../../../shared/components/quiet-button/quiet-action-button.component';
import { getDateTimeInISOAndUTCOffsetFormat } from '../../../../shared/utils';
import { UpdatePersonalAccessTokenDialog } from './update-personal-access-token-dialog.component';
import { checkIfTokenOwner } from './utils';

interface PersonalAccessTokenMenuProps {
    token: PartialPersonalAccessToken;
}

enum PersonalAccessTokenMenuItems {
    EDIT = 'Edit',
    DELETE = 'Delete',
}

export const PersonalAccessTokenMenu = ({ token }: PersonalAccessTokenMenuProps): JSX.Element => {
    const deleteTriggerState = useOverlayTriggerState({});
    const editTriggerState = useOverlayTriggerState({});
    const { deletePersonalAccessTokenMutation, updatePersonalAccessTokenMutation } = usePersonalAccessToken();
    const { organizationId } = useOrganizationIdentifier();
    const { useActiveUser } = useUsers();
    const { data: activeUser } = useActiveUser(organizationId);
    const hasActiveUser = activeUser?.id;

    if (!hasActiveUser) {
        return <></>;
    }

    const isTokenOwner = checkIfTokenOwner(token, activeUser.id);

    if (!isTokenOwner) {
        return <></>;
    }

    const handleEdit = (newDate: Date): void => {
        const expiresAt = getDateTimeInISOAndUTCOffsetFormat(dayjs(newDate).endOf('d'));
        if (hasActiveUser) {
            updatePersonalAccessTokenMutation.mutate({
                organizationId,
                userId: activeUser.id,
                tokenId: token.id,
                expirationDate: expiresAt,
            });
        }
    };

    const handleDelete = (): void => {
        if (hasActiveUser) {
            deletePersonalAccessTokenMutation.mutate({ organizationId, userId: activeUser.id, tokenId: token.id });
        }
    };

    const handleOnAction = (key: Key): void => {
        if (key === PersonalAccessTokenMenuItems.DELETE) {
            deleteTriggerState.open();
        } else if (key === PersonalAccessTokenMenuItems.EDIT) {
            editTriggerState.open();
        }
    };

    return (
        <>
            <MenuTrigger>
                <QuietActionButton id={`personal-access-token-menu-${token.id}-button`}>
                    <MoreMenu />
                </QuietActionButton>
                <Menu id={`${token.id}-menu-id`} onAction={handleOnAction}>
                    <Item key={PersonalAccessTokenMenuItems.EDIT} textValue='Update'>
                        <Text>
                            <Flex alignItems={'center'} justifyContent={'space-between'} gap={'size-300'}>
                                <Flex alignItems={'center'} gap={'size-125'}>
                                    <Edit />
                                    <Text>Edit</Text>
                                </Flex>
                            </Flex>
                        </Text>
                    </Item>
                    <Item key={PersonalAccessTokenMenuItems.DELETE} textValue='Delete'>
                        <Text>
                            <Flex alignItems={'center'} justifyContent={'space-between'} gap={'size-300'}>
                                <Flex alignItems={'center'} gap={'size-125'}>
                                    <Delete />
                                    <Text>Delete</Text>
                                </Flex>
                            </Flex>
                        </Text>
                    </Item>
                </Menu>
            </MenuTrigger>
            <UpdatePersonalAccessTokenDialog token={token} onAction={handleEdit} triggerState={editTriggerState} />
            <DeleteDialog
                title={'Personal Access Token'}
                name={token.name}
                onAction={handleDelete}
                triggerState={deleteTriggerState}
            />
        </>
    );
};
