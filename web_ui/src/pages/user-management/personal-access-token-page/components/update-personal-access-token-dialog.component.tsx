// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

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
import { Button } from '@shared/components/button/button.component';
import { OverlayTriggerState } from 'react-stately';

import { PartialPersonalAccessToken } from '../../../../core/personal-access-tokens/personal-access-tokens.interface';
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
