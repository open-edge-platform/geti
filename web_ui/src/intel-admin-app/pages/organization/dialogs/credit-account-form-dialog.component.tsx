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
    Checkbox,
    Content,
    Dialog,
    DialogContainer,
    Divider,
    Flex,
    Form,
    Heading,
    NumberField,
    TextField,
} from '@adobe/react-spectrum';
import { DateValue, getLocalTimeZone, parseAbsolute, parseDate, today } from '@internationalized/date';
import dayjs from 'dayjs';

import { CreditAccount, NewCreditAccount } from '../../../../core/credits/credits.interface';
import { Button } from '../../../../shared/components/button/button.component';
import { DatePicker } from '../../../../shared/components/date-picker/date-picker.component';
import { useOrganization } from '../hooks/organization.hook';

import classes from './dialogs.module.scss';

interface CreditAccountCreateEditDialogProps {
    onSave: (creditAccount: NewCreditAccount) => void;
    isOpen: boolean;
    onOpenChange: (isOpen: boolean) => void;
    isLoading?: boolean;
}

interface CreditAccountCreateDialogProps extends CreditAccountCreateEditDialogProps {
    isNew: true;
}

interface CreditAccountEditDialogProps extends CreditAccountCreateEditDialogProps {
    isNew?: false;
    creditAccount: CreditAccount;
}

interface CreditAccountFormState {
    name: string;
    isRenewable: boolean;
    amount: number | undefined;
    renewableDay: number | undefined;
    expires: DateValue | undefined;
}

const MIN_DATE = today(getLocalTimeZone());
const MAX_DATE = parseDate('9999-11-30');

export const CreditAccountFormDialog = (
    props: CreditAccountCreateDialogProps | CreditAccountEditDialogProps
): JSX.Element => {
    const { isNew, isOpen, onOpenChange, onSave, isLoading } = props;
    const { organizationId } = useOrganization();

    const initFormState = (): CreditAccountFormState => {
        if (isNew) {
            return {
                name: '',
                amount: 500,
                isRenewable: false,
                renewableDay: new Date().getDate(),
                expires: undefined,
            };
        } else {
            return {
                name: props.creditAccount.name,
                amount: props.creditAccount.renewableAmount,
                isRenewable: props.creditAccount.type === 'renewable',
                renewableDay: props.creditAccount.renewalDayOfMonth,
                expires: props.creditAccount.expires
                    ? parseAbsolute(dayjs(props.creditAccount.expires).toISOString(), getLocalTimeZone())
                    : undefined,
            };
        }
    };

    const [creditAccountState, setCreditAccountState] = useState(initFormState);

    const onChangeField = (field: keyof CreditAccountFormState, value: unknown): void => {
        setCreditAccountState((prevState) => ({
            ...prevState,
            [field]: value,
            isEdited: true,
        }));
    };

    const onFormSubmit = (event: React.FormEvent<HTMLFormElement>): void => {
        event.preventDefault();
        const newCreditAccount = {
            name: creditAccountState.name,
            organizationId: !isNew ? props.creditAccount.organizationId : organizationId,
            initAmount: isNew && !Number.isNaN(creditAccountState.amount) ? creditAccountState.amount : undefined,
            expires: creditAccountState.expires?.toDate(getLocalTimeZone()).getTime(),
        };
        if (creditAccountState.isRenewable) {
            onSave({
                ...newCreditAccount,
                renewableAmount: creditAccountState.amount,
                renewalDayOfMonth: creditAccountState.renewableDay,
            });
        } else {
            onSave({
                ...newCreditAccount,
            });
        }
    };

    return (
        <DialogContainer onDismiss={() => isLoading !== true && onOpenChange(false)}>
            {isOpen && (
                <Dialog>
                    <Heading level={2}>{isNew ? 'Create' : 'Edit'} credit account</Heading>
                    <Divider size={'S'} />
                    <Content>
                        <Form onSubmit={onFormSubmit} validationBehavior='native'>
                            <TextField
                                label='Name'
                                name='name'
                                // eslint-disable-next-line jsx-a11y/no-autofocus
                                autoFocus
                                id='credit-account-name-text-field'
                                value={creditAccountState.name}
                                onChange={(value) => onChangeField('name', value)}
                                isRequired
                            />
                            <Flex gap='size-200' alignItems={'end'}>
                                <NumberField
                                    value={creditAccountState.amount}
                                    onChange={(value) => onChangeField('amount', value)}
                                    isDisabled={!isNew && !creditAccountState.isRenewable}
                                    minValue={isNew || creditAccountState.isRenewable ? 1 : undefined}
                                    maxValue={Number.MAX_SAFE_INTEGER}
                                    isRequired={isNew || creditAccountState.isRenewable}
                                    label='Amount'
                                    name='amount'
                                    id='credit-account-amount-number-field'
                                    width={'50%'}
                                    hideStepper
                                />
                                <Checkbox
                                    isSelected={creditAccountState.isRenewable}
                                    onChange={(value) => onChangeField('isRenewable', value)}
                                    isDisabled={!isNew}
                                    id='credit-account-renawable-checkbox'
                                    width={'50%'}
                                >
                                    Renewable
                                </Checkbox>
                            </Flex>
                            <DatePicker
                                label='Expiration date'
                                value={creditAccountState.expires}
                                onChange={(value) => onChangeField('expires', value)}
                                minValue={MIN_DATE}
                                maxValue={MAX_DATE}
                                id='credit-account-expiration-date-picker'
                                width={'100%'}
                                granularity='day'
                            />
                            <ButtonGroup UNSAFE_className={classes.dialogFormButtonGroup}>
                                <Button
                                    variant='secondary'
                                    onPress={() => onOpenChange(false)}
                                    isDisabled={isLoading}
                                    id='credit-account-cancel-button'
                                >
                                    Cancel
                                </Button>
                                <Button
                                    variant='accent'
                                    type='submit'
                                    id='credit-account-save-button'
                                    isPending={isLoading}
                                >
                                    Save
                                </Button>
                            </ButtonGroup>
                        </Form>
                    </Content>
                </Dialog>
            )}
        </DialogContainer>
    );
};
