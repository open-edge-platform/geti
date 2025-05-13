// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { ButtonGroup, Content, Dialog, DialogContainer, Divider, Flex, Heading, Text } from '@adobe/react-spectrum';
import { dimensionValue } from '@react-spectrum/utils';
import { noop } from 'lodash-es';

import { Alert } from '../../../../assets/icons';
import { Button } from '../../button/button.component';

import classes from './jobs.module.scss';

interface JobCancellationWarningProps {
    totalCreditsConsumed: number;
    isOpen: boolean;
    isPrimaryActionDisabled: boolean;
    shouldShowLostCreditsContent: boolean;
    jobName?: string;
    setIsOpen: (isOpen: boolean) => void;
    onPrimaryAction: () => void;
}

export const JobCancellationWarning = ({
    totalCreditsConsumed,
    isOpen,
    isPrimaryActionDisabled,
    shouldShowLostCreditsContent,
    jobName,
    setIsOpen,
    onPrimaryAction,
}: JobCancellationWarningProps) => {
    return (
        <DialogContainer type={'modal'} onDismiss={noop}>
            {isOpen && (
                <Dialog width={{ base: 'auto', L: '74rem' }} id={`cancel-job-dialog`} role='alertdialog'>
                    <Heading>Cancel job</Heading>

                    <Divider />

                    {shouldShowLostCreditsContent ? (
                        <Content>
                            <Flex
                                UNSAFE_className={classes.costWarningContainer}
                                gap={'size-115'}
                                alignItems={'center'}
                            >
                                <Alert />
                                <Text UNSAFE_style={{ fontWeight: 700 }}>{totalCreditsConsumed} credits</Text> for this
                                job &quot;{jobName}&quot; will not be refunded if cancelled.
                            </Flex>

                            <Text
                                marginTop={'size-275'}
                                UNSAFE_style={{ display: 'block', fontSize: dimensionValue('size-225') }}
                            >
                                Are you sure you want to cancel job &quot;{jobName}&quot; and lose{' '}
                                {totalCreditsConsumed} credits?
                            </Text>

                            <Divider size={'S'} marginTop={'size-150'} />
                        </Content>
                    ) : (
                        <Content>
                            <Text>Are you sure you want to cancel job &quot;{jobName}&quot;?</Text>
                        </Content>
                    )}

                    <ButtonGroup>
                        <Button
                            variant={'primary'}
                            onPress={() => setIsOpen(false)}
                            id='cancel-job-modal-no-button'
                            aria-label='Close cancel job dialog'
                        >
                            Dismiss
                        </Button>
                        <Button
                            isDisabled={isPrimaryActionDisabled}
                            variant={'negative'}
                            onPress={onPrimaryAction}
                            id='cancel-job-modal-yes-button'
                            aria-label='Cancel job'
                        >
                            Cancel
                        </Button>
                    </ButtonGroup>
                </Dialog>
            )}
        </DialogContainer>
    );
};
