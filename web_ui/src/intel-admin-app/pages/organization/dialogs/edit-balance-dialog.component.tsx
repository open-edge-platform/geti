// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { useEffect, useState } from 'react';

import {
    ActionGroup,
    ButtonGroup,
    Content,
    Dialog,
    DialogContainer,
    Divider,
    Form,
    Heading,
    Item,
    NumberField,
    TextField,
} from '@adobe/react-spectrum';
import { Button } from '@geti/ui';

import { CreditAccountBalance, NewCreditAccountBalance } from '../../../../core/credits/credits.interface';

import classes from './dialogs.module.scss';

enum BalanceActionType {
    ADD = 'Add',
    SUBTRACT = 'Subtract',
}

interface EditCreditAccountBalanceDialogProps {
    onSave: (balance: NewCreditAccountBalance) => void;
    balance: CreditAccountBalance;
    isOpen: boolean;
    onOpenChange: (isOpen: boolean) => void;
    isLoading?: boolean;
}

export const EditCreditAccountBalanceDialog = (props: EditCreditAccountBalanceDialogProps) => {
    const { balance, onSave, isOpen, onOpenChange, isLoading } = props;

    const [delta, setDelta] = useState(0);

    const [actionSelected, setActionSelected] = useState(BalanceActionType.ADD);

    const getResultingBalance = (): number => {
        if (actionSelected === BalanceActionType.ADD) {
            return balance.available + delta;
        }

        return Math.max(0, balance.available - delta);
    };

    useEffect(() => {
        if (isOpen) {
            setDelta(0);
            setActionSelected(BalanceActionType.ADD);
        }
    }, [isOpen]);

    return (
        <DialogContainer onDismiss={() => isLoading !== true && onOpenChange(false)}>
            {isOpen && (
                <Dialog>
                    <Heading level={2}>Edit balance</Heading>
                    <Divider size={'S'} />
                    <Content>
                        <Form>
                            <TextField
                                label={'Available credits'}
                                value={balance.available.toString()}
                                UNSAFE_className={classes.textFieldReadOnly}
                                id={'credit-account-available-credits-input'}
                                isReadOnly
                            />
                            <ActionGroup
                                density='compact'
                                selectionMode='single'
                                items={[
                                    { id: BalanceActionType.ADD, label: BalanceActionType.ADD },
                                    { id: BalanceActionType.SUBTRACT, label: BalanceActionType.SUBTRACT },
                                ]}
                                selectedKeys={[actionSelected]}
                                onAction={(value) => setActionSelected(value as BalanceActionType)}
                                UNSAFE_className={classes.balanceActionGroup}
                                isEmphasized
                                disallowEmptySelection
                            >
                                {(item) => <Item>{item.label}</Item>}
                            </ActionGroup>
                            <NumberField
                                label={'Balance'}
                                name={'balance'}
                                // eslint-disable-next-line jsx-a11y/no-autofocus
                                autoFocus
                                onFocus={(event) => {
                                    (event.target as HTMLInputElement).select();
                                }}
                                id={'credit-account-edit-balance-numberfield'}
                                value={delta}
                                minValue={0}
                                maxValue={
                                    actionSelected === BalanceActionType.SUBTRACT
                                        ? balance.available
                                        : Number.MAX_SAFE_INTEGER
                                }
                                onChange={(value: number) => setDelta(value)}
                                UNSAFE_className={
                                    actionSelected === BalanceActionType.ADD
                                        ? classes.balanaceFieldAdd
                                        : classes.balanaceFieldSubtract
                                }
                                hideStepper
                            />
                            <TextField
                                label={'Resulting amount of available credits'}
                                value={getResultingBalance().toString()}
                                UNSAFE_className={classes.textFieldReadOnly}
                                id={'credit-account-remaining-balance-input'}
                                isReadOnly
                            />
                        </Form>
                    </Content>
                    <ButtonGroup>
                        <Button variant='secondary' onPress={() => onOpenChange(false)}>
                            Cancel
                        </Button>
                        <Button
                            variant='accent'
                            onPress={() => {
                                onSave(actionSelected === BalanceActionType.ADD ? { add: delta } : { subtract: delta });
                            }}
                            isPending={isLoading}
                            isDisabled={delta === 0}
                            id={'credit-account-edit-balance-save-button'}
                        >
                            Save
                        </Button>
                    </ButtonGroup>
                </Dialog>
            )}
        </DialogContainer>
    );
};
