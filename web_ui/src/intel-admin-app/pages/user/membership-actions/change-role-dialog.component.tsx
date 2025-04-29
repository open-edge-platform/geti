// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { FC, Key, useState } from 'react';

import {
    ButtonGroup,
    Content,
    Dialog,
    DialogContainer,
    Divider,
    Flex,
    Heading,
    Item,
    Picker,
} from '@adobe/react-spectrum';

import { RESOURCE_TYPE, RoleResource, USER_ROLE } from '../../../../core/users/users.interface';
import { Button } from '../../../../shared/components/button/button.component';
import { PhotoPlaceholder } from '../../../../shared/components/photo-placeholder/photo-placeholder.component';
import { TruncatedText } from '../../../../shared/components/truncated-text/truncated-text.component';
import { Membership } from '../mocked-memberships';

interface ChangeRoleDialogInnerProps {
    onCancel: () => void;
    membership: Membership;
}

const ChangeRoleDialogInner: FC<ChangeRoleDialogInnerProps> = ({ membership, onCancel }) => {
    const [selectedRole, setSelectedRole] = useState<USER_ROLE>(membership.role);

    const roles: RoleResource[] = [
        {
            role: USER_ROLE.ORGANIZATION_ADMIN,
            resourceId: membership.organizationId,
            resourceType: RESOURCE_TYPE.ORGANIZATION,
        },
        {
            role: USER_ROLE.ORGANIZATION_CONTRIBUTOR,
            resourceId: membership.organizationId,
            resourceType: RESOURCE_TYPE.ORGANIZATION,
        },
    ];

    const handleChangeRole = (key: Key) => {
        const newRole = key as USER_ROLE;

        setSelectedRole(newRole);
    };

    const handleSaveRole = () => {
        //
    };

    return (
        <Dialog>
            <Heading>Change role</Heading>
            <Divider />
            <Content>
                <Flex alignItems={'center'} gap={'size-100'} marginBottom={'size-250'} marginTop={'size-150'}>
                    <PhotoPlaceholder
                        name={membership.organizationName}
                        email={membership.organizationName}
                        width={'size-300'}
                        height={'size-300'}
                    />
                    <TruncatedText>{membership.organizationName}</TruncatedText>
                </Flex>
                <Picker
                    label={'Role'}
                    items={roles}
                    width={'100%'}
                    selectedKey={selectedRole}
                    onSelectionChange={handleChangeRole}
                >
                    {(item) => <Item key={item.role}>{item.role}</Item>}
                </Picker>
            </Content>
            <ButtonGroup>
                <Button onPress={onCancel} variant={'secondary'}>
                    Cancel
                </Button>
                <Button onPress={handleSaveRole}>Save</Button>
            </ButtonGroup>
        </Dialog>
    );
};

interface ChangeRoleDialogProps {
    isOpen: boolean;
    membership: Membership;
    onCancel: () => void;
}

export const ChangeRoleDialog: FC<ChangeRoleDialogProps> = ({ isOpen, membership, onCancel }) => {
    return (
        <DialogContainer onDismiss={onCancel}>
            {isOpen && <ChangeRoleDialogInner membership={membership} onCancel={onCancel} />}
        </DialogContainer>
    );
};
