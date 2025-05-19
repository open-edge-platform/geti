// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { useEffect, useState } from 'react';

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
import { Button } from '@geti/ui';
import dayjs from 'dayjs';

import { usePersonalAccessToken } from '../../../../core/personal-access-tokens/hooks/use-personal-access-token.hook';
import { CreatePersonalAccessTokenDialogProps } from '../../../../core/personal-access-tokens/personal-access-tokens.interface';
import { WarningMessage } from '../../../../shared/components/warning-message/warning-message.component';
import { getDateTimeInISOAndUTCOffsetFormat } from '../../../../shared/utils';
import { CopyPersonalAccessToken } from './copy-personal-access-token.component';
import { PersonalAccessTokenExpirationDatepicker } from './personal-access-token-expiration-datepicker.component';

import classes from '../personal-access-token-page.module.scss';

enum Steps {
    Copy,
    ExpirationDate,
}

// NOTE: values set on backend side
const NAME_MAX_LENGTH = 100;
const DESCRIPTION_MAX_LENGTH = 1000;

interface PersonalAccessTokenData {
    name: string;
    description: string;
    expirationDate: Date | null;
}

export const CreatePersonalAccessTokenDialog = ({
    organizationId,
    userId,
    triggerState,
}: CreatePersonalAccessTokenDialogProps) => {
    const { createPersonalAccessTokenMutation } = usePersonalAccessToken();

    const [currentStep, setCurrentStep] = useState(Steps.ExpirationDate);
    const [personalAccessTokenData, setPersonalAccessTokenData] = useState<PersonalAccessTokenData>({
        name: '',
        description: '',
        expirationDate: null,
    });

    const isCopy = Steps.Copy === currentStep;
    const isExpirationDate = Steps.ExpirationDate === currentStep;
    const isFetchingPersonalAccessToken = isExpirationDate && createPersonalAccessTokenMutation.isPending;
    const isCreateButtonDisabled =
        !personalAccessTokenData.expirationDate || !personalAccessTokenData.name || isFetchingPersonalAccessToken;

    const onSendRequest = () => {
        const expiresAt = getDateTimeInISOAndUTCOffsetFormat(dayjs(personalAccessTokenData.expirationDate).endOf('d'));

        createPersonalAccessTokenMutation.mutate(
            {
                name: personalAccessTokenData.name,
                description: personalAccessTokenData.description,
                expirationDate: expiresAt,
                organizationId,
                userId,
            },
            {
                onSuccess: () => setCurrentStep(Steps.Copy),
            }
        );
    };

    useEffect(() => {
        if (!triggerState.isOpen) {
            setPersonalAccessTokenData({ name: '', description: '', expirationDate: null });
            setCurrentStep(Steps.ExpirationDate);
        }
    }, [triggerState.isOpen]);

    return (
        <DialogContainer onDismiss={triggerState.close}>
            {triggerState.isOpen && (
                <Dialog aria-label='api-key-dialog'>
                    <Heading UNSAFE_className={classes.dialogHeading}>Personal Access Token</Heading>

                    <Divider marginY={'size-250'} />

                    <Content>
                        <View UNSAFE_className={classes.personalAccessTokenDialogBody}>
                            {isExpirationDate && (
                                <>
                                    <TextField
                                        label={'Name'}
                                        id={'pat-name-id'}
                                        onChange={(newName) => {
                                            setPersonalAccessTokenData({ ...personalAccessTokenData, name: newName });
                                        }}
                                        width={'100%'}
                                        isRequired
                                        maxLength={NAME_MAX_LENGTH}
                                    />
                                    <TextField
                                        width={'100%'}
                                        label={'Description'}
                                        id={'pat-description-id'}
                                        onChange={(newDescription) => {
                                            setPersonalAccessTokenData({
                                                ...personalAccessTokenData,
                                                description: newDescription,
                                            });
                                        }}
                                        maxLength={DESCRIPTION_MAX_LENGTH}
                                    />
                                    <PersonalAccessTokenExpirationDatepicker
                                        setDate={(newExpirationDate) => {
                                            setPersonalAccessTokenData({
                                                ...personalAccessTokenData,
                                                expirationDate: newExpirationDate,
                                            });
                                        }}
                                    />
                                </>
                            )}
                            {isCopy && (
                                <CopyPersonalAccessToken
                                    personalAccessToken={createPersonalAccessTokenMutation.data?.personalAccessToken}
                                    personalAccessTokenId={createPersonalAccessTokenMutation.data?.id}
                                />
                            )}
                        </View>

                        <Divider size='S' marginY={'size-300'} />

                        {isCopy && (
                            <WarningMessage
                                isVisible
                                message={`
                                    You won't be able to retrieve the Personal Access Token after closing this dialog.
                                `}
                                marginTop={'size-275'}
                                id={'copy-warning-message-id'}
                            />
                        )}
                    </Content>

                    <ButtonGroup UNSAFE_style={{ padding: 0 }}>
                        <Button id={'close-cancel-button-id'} variant='secondary' onPress={triggerState.close}>
                            {isCopy ? 'Close' : 'Cancel'}
                        </Button>
                        {isExpirationDate && (
                            <Button
                                variant='accent'
                                id={'create-api-token-button-id'}
                                isPending={isFetchingPersonalAccessToken}
                                isDisabled={isCreateButtonDisabled}
                                onPress={onSendRequest}
                            >
                                Create
                            </Button>
                        )}
                    </ButtonGroup>
                </Dialog>
            )}
        </DialogContainer>
    );
};
