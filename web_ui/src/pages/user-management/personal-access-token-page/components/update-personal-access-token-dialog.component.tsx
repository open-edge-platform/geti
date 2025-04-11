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

import { useState } from 'react';

import {
    ButtonGroup,
    Content,
    Dialog,
    DialogContainer,
    Divider,
    Heading,
    TextField,
    View,
} from '@adobe/react-spectrum';
import { OverlayTriggerState } from 'react-stately';

import { PartialPersonalAccessToken } from '../../../../core/personal-access-tokens/personal-access-tokens.interface';
import { Button } from '../../../../shared/components/button/button.component';
import { PersonalAccessTokenExpirationDatepicker } from './personal-access-token-expiration-datepicker.component';

import classes from '../personal-access-token-page.module.scss';

interface UpdatePersonalAccessTokenDialogProps {
    triggerState: OverlayTriggerState;
    token: PartialPersonalAccessToken;
    onAction: (newDate: Date) => void;
}

export const UpdatePersonalAccessTokenDialog = ({
    triggerState,
    token,
    onAction,
}: UpdatePersonalAccessTokenDialogProps) => {
    const [newDate, setNewDate] = useState<Date | null>(null);
    const isUpdateButtonDisabled = !newDate;

    const onSendRequest = () => {
        triggerState.close();
        newDate && onAction(newDate);
    };

    return (
        <DialogContainer onDismiss={triggerState.close}>
            {triggerState.isOpen && (
                <Dialog aria-label='update-token-dialog'>
                    <Heading UNSAFE_className={classes.dialogHeading}>Personal Access Token</Heading>
                    <Divider marginY={'size-250'} />
                    <Content UNSAFE_style={{ overflow: 'visible' }}>
                        <View UNSAFE_className={classes.personalAccessTokenDialogBody}>
                            <TextField label={'Name'} isDisabled placeholder={token.name} width={'100%'} />
                            <TextField
                                label={'Description'}
                                isDisabled
                                placeholder={token.description}
                                width={'100%'}
                            />
                            <PersonalAccessTokenExpirationDatepicker
                                setDate={(newExpirationDate) => {
                                    setNewDate(newExpirationDate);
                                }}
                                placeholderDate={token.expiresAt.split('T')[0]}
                            />
                        </View>
                        <Divider size='S' marginY={'size-300'} />
                    </Content>
                    <ButtonGroup UNSAFE_style={{ padding: 0 }}>
                        <Button id={'close-cancel-button-id'} variant='secondary' onPress={triggerState.close}>
                            Cancel
                        </Button>
                        <Button
                            variant='accent'
                            id={'update-token-button-id'}
                            isDisabled={isUpdateButtonDisabled}
                            onPress={onSendRequest}
                        >
                            Update
                        </Button>
                    </ButtonGroup>
                </Dialog>
            )}
        </DialogContainer>
    );
};
