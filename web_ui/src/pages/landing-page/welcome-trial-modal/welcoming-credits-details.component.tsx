// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { Divider, Flex, Text, useNumberFormatter, View } from '@geti/ui';

import classes from './welcome-trial-modal.module.scss';

interface WelcomingCreditsProps {
    initCredits: number | null;
    monthlyRenewalCredits: number | null;
}

const WelcomingCredits = ({ initCredits, monthlyRenewalCredits }: WelcomingCreditsProps) => {
    const numberFormatter = useNumberFormatter({});

    return (
        <ul>
            {initCredits !== null && (
                <li>
                    <Text UNSAFE_className={classes.credits}>
                        <Text data-testid={`init-credits-${initCredits}-id`} id={`init-credits-${initCredits}-id`}>
                            Kick off your journey with{' '}
                            <span className={classes.blue}>{numberFormatter.format(initCredits)} free credits</span> as
                            welcome gift.
                        </Text>
                    </Text>
                </li>
            )}

            {monthlyRenewalCredits !== null && (
                <li>
                    <Text UNSAFE_className={classes.credits}>
                        <Text
                            data-testid={`renewable-credits-${monthlyRenewalCredits}-id`}
                            id={`renewable-credits-${monthlyRenewalCredits}-id`}
                        >
                            Your team will receive{' '}
                            <span className={classes.blue}>
                                {numberFormatter.format(monthlyRenewalCredits)} free credits
                            </span>{' '}
                            as to use every month.
                        </Text>
                    </Text>
                </li>
            )}
        </ul>
    );
};

export const WelcomingCreditsDetails = ({ initCredits, monthlyRenewalCredits }: WelcomingCreditsProps) => {
    return (
        <View
            backgroundColor='gray-200'
            width='100%'
            paddingY='size-300'
            paddingX='size-500'
            UNSAFE_style={{ boxSizing: 'border-box' }}
        >
            <Flex direction='column' gap='size-200' width='100%' alignItems='center'>
                <WelcomingCredits initCredits={initCredits} monthlyRenewalCredits={monthlyRenewalCredits} />

                <Divider size='S' UNSAFE_className={classes.divider} />

                <Text UNSAFE_className={classes.creditValue}>1 credit = 1 image used for model training</Text>
            </Flex>
        </View>
    );
};
