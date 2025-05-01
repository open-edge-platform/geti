// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { ButtonGroup, Content, Dialog, DialogContainer, Divider, Flex, Heading, Text } from '@adobe/react-spectrum';
import { dimensionValue } from '@react-spectrum/utils';
import { Button } from '@shared/components/button/button.component';
import { openNewTab } from '@shared/utils';
import noop from 'lodash/noop';

import { CreditCard } from '../../../../../assets/icons';
import { CONTACT_SUPPORT } from '../../../../../core/const';
import { NotEnoughWarning } from '../not-enough-warning/not-enough-warning.component';

import classes from './not-enough-credits-dialog.module.scss';

interface NotEnoughCreditsDialogProps {
    isOpen: boolean;
    onClose: () => void;
    creditsAvailable: number;
    creditsToConsume: number;
    message: {
        body: string;
        header: string;
    };
}

export const NotEnoughCreditsDialog = ({
    isOpen,
    message,
    creditsAvailable,
    creditsToConsume,
    onClose,
}: NotEnoughCreditsDialogProps): JSX.Element => {
    return (
        <DialogContainer type={'modal'} onDismiss={noop}>
            {isOpen && (
                <Dialog width={{ base: 'auto', L: '74rem' }}>
                    <Heading>Not enough credits</Heading>

                    <Divider />

                    <Content>
                        <NotEnoughWarning>
                            <Flex gap={'size-115'} direction={'column'}>
                                <Text>
                                    {message.header} <Text UNSAFE_style={{ fontWeight: 700 }}>{creditsToConsume} </Text>
                                    credits
                                </Text>

                                <Flex
                                    UNSAFE_className={classes.costWarningBalance}
                                    gap={'size-115'}
                                    alignItems={'center'}
                                >
                                    <CreditCard />
                                    Available: {creditsAvailable} credits
                                </Flex>
                            </Flex>
                        </NotEnoughWarning>

                        <Text
                            marginTop={'size-275'}
                            UNSAFE_style={{ display: 'block', fontSize: dimensionValue('size-200') }}
                        >
                            {message.body}
                        </Text>

                        <Divider size={'S'} marginTop={'size-150'} />
                    </Content>

                    <ButtonGroup>
                        <Button variant={'primary'} onPress={onClose} id={'close-not-enough-credits-modal'}>
                            Close
                        </Button>
                        <Button
                            variant={'accent'}
                            id={'concat-support-credits-modal'}
                            onPress={() => {
                                onClose();
                                openNewTab(CONTACT_SUPPORT);
                            }}
                        >
                            Contact support
                        </Button>
                    </ButtonGroup>
                </Dialog>
            )}
        </DialogContainer>
    );
};
