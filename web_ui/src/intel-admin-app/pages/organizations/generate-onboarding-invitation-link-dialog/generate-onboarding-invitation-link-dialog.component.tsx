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

import { FC, useState } from 'react';

import { ButtonGroup, Content, Dialog, DialogContainer, Divider, Heading } from '@adobe/react-spectrum';
import { DateValue, getLocalTimeZone, today } from '@internationalized/date';
import { useOverlayTriggerState } from '@react-stately/overlays';
import { RangeValue } from '@react-types/shared';

import { useGenerateOnboardingTokenMutation } from '../../../../core/users/hook/use-generate-onboarding-token.hook';
import { Button } from '../../../../shared/components/button/button.component';
import { DateRangePicker } from '../../../../shared/components/date-range-picker/date-range-picker.component';
import { CopyOnboardingInvitationLink } from './copy-onboarding-invitation-link.component';

enum GenerateTokenSteps {
    DATES_PICKER,
    COPY_TOKEN,
}

const INITIAL_STEP = GenerateTokenSteps.DATES_PICKER;

interface GenerateOnboardingTokenDialogProps {
    onDismissDialog: () => void;
}

const GenerateOnboardingTokenDialog: FC<GenerateOnboardingTokenDialogProps> = ({ onDismissDialog }) => {
    const TODAY = today(getLocalTimeZone());
    const INITIAL_DATES: RangeValue<DateValue> = {
        start: TODAY,
        end: TODAY.add({ days: 30 }),
    };

    const [step, setStep] = useState<GenerateTokenSteps>(INITIAL_STEP);

    const [datesRange, setDatesRange] = useState<RangeValue<DateValue> | null>(INITIAL_DATES);
    const generateOnboardingTokenMutation = useGenerateOnboardingTokenMutation();

    const isDatesPickerStep = step === GenerateTokenSteps.DATES_PICKER;

    const handleGenerateToken = () => {
        if (datesRange === null) {
            return;
        }

        generateOnboardingTokenMutation.mutate(
            {
                dateTo: datesRange.end.toString(),
                dateFrom: datesRange.start.toString(),
            },
            {
                onSuccess: () => {
                    setStep(GenerateTokenSteps.COPY_TOKEN);
                },
            }
        );
    };

    return (
        <Dialog size={'M'}>
            <Heading>{isDatesPickerStep ? 'Create invitation link' : 'Copy invitation link'}</Heading>
            <Divider />
            <Content>
                {isDatesPickerStep && (
                    <DateRangePicker
                        label={'Dates range'}
                        startName='startDate'
                        endName='endDate'
                        value={datesRange}
                        onChange={setDatesRange}
                        minValue={TODAY}
                    />
                )}
                {step === GenerateTokenSteps.COPY_TOKEN &&
                    generateOnboardingTokenMutation.data?.onboardingToken !== undefined && (
                        <CopyOnboardingInvitationLink
                            onboardingToken={generateOnboardingTokenMutation.data?.onboardingToken}
                        />
                    )}
            </Content>
            <ButtonGroup>
                <Button variant={'secondary'} onPress={onDismissDialog}>
                    {isDatesPickerStep ? 'Cancel' : 'Close'}
                </Button>
                {isDatesPickerStep && (
                    <Button onPress={handleGenerateToken} isPending={generateOnboardingTokenMutation.isPending}>
                        Generate
                    </Button>
                )}
            </ButtonGroup>
        </Dialog>
    );
};

export const GenerateOnboardingTokenDialogContainer = (): JSX.Element => {
    const { isOpen, setOpen } = useOverlayTriggerState({});

    const handleOpenDialog = () => {
        setOpen(true);
    };

    const handleDismissDialog = () => {
        setOpen(false);
    };

    return (
        <>
            <Button variant={'primary'} onPress={handleOpenDialog}>
                Create invitation link
            </Button>
            <DialogContainer onDismiss={handleDismissDialog}>
                {isOpen && <GenerateOnboardingTokenDialog onDismissDialog={handleDismissDialog} />}
            </DialogContainer>
        </>
    );
};
