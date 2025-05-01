// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { FC, useState } from 'react';

import { ButtonGroup, Content, Dialog, DialogContainer, Divider, Heading } from '@adobe/react-spectrum';
import { DateValue, getLocalTimeZone, today } from '@internationalized/date';
import { useOverlayTriggerState } from '@react-stately/overlays';
import { RangeValue } from '@react-types/shared';
import { Button } from '@shared/components/button/button.component';
import { DateRangePicker } from '@shared/components/date-range-picker/date-range-picker.component';

import { useGenerateOnboardingTokenMutation } from '../../../../core/users/hook/use-generate-onboarding-token.hook';
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
