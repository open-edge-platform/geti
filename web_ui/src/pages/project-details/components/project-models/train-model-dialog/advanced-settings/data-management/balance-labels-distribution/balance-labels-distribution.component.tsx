// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { FC, useState } from 'react';

import { Content, ContextualHelp, Flex, Grid, Heading, Text, View } from '@adobe/react-spectrum';
import isEmpty from 'lodash/isEmpty';
import { useNumberFormatter } from 'react-aria';

import { Switch } from '../../../../../../../../shared/components/switch/switch.component';
import { Accordion } from '../../ui/accordion/accordion.component';

import styles from './balance-labels-distribution.module.scss';

interface Label {
    name: string;
    count: number;
    totalCount: number;
    color: string;
}

interface LabelDistributionProps {
    label: Label;
}

const LabelDistribution: FC<LabelDistributionProps> = ({ label }) => {
    const { name, count, totalCount, color } = label;
    const value = (count / totalCount) * 100;
    const formatOptions = {
        style: 'percent',
        maximumFractionDigits: 2,
    } as const;

    const formatter = useNumberFormatter(formatOptions);
    const valueInPercent = formatter.format(value / 100);

    return (
        <>
            <Heading level={4} margin={0}>
                {name}
            </Heading>
            <Flex alignItems={'center'}>
                <View
                    UNSAFE_style={{
                        backgroundColor: color,
                        width: valueInPercent,
                    }}
                    UNSAFE_className={styles.meter}
                />
                <Text marginStart={'size-50'}>
                    {count} <Text UNSAFE_className={styles.labelCountPercent}>({valueInPercent})</Text>
                </Text>
            </Flex>
        </>
    );
};

interface LabelsDistributionProps {
    labels: Label[];
}

const LabelsDistribution: FC<LabelsDistributionProps> = ({ labels }) => {
    return (
        <View>
            <Text UNSAFE_className={styles.title} marginBottom={'size-250'}>
                Labels distribution
            </Text>
            <Grid columns={['max-content', '1fr']} columnGap={'size-450'} rowGap={'size-100'}>
                {labels.map((label) => (
                    <LabelDistribution key={label.name} label={label} />
                ))}
            </Grid>
        </View>
    );
};

const BalanceLabelsDistributionTooltip: FC = () => {
    return (
        <ContextualHelp variant='info'>
            <Content>
                <Text>
                    This option creates another dataset (Balanced set), it does not alter the original dataset. The new
                    balanced dataset does not occupy additional storage.
                </Text>
            </Content>
        </ContextualHelp>
    );
};

export const BalanceLabelsDistribution: FC = () => {
    const [isEnabled, setIsEnabled] = useState<boolean>(false);

    const labels: LabelsDistributionProps['labels'] = [
        {
            name: 'Label 1',
            count: 6,
            totalCount: 102,
            color: 'red',
        },
        {
            name: 'Label 2',
            count: 24,
            totalCount: 102,
            color: 'blue',
        },
        {
            name: 'Label 3',
            count: 30,
            totalCount: 102,
            color: 'green',
        },
        {
            name: 'Label 4',
            count: 42,
            totalCount: 102,
            color: 'yellow',
        },
    ];

    if (isEmpty(labels)) {
        return null;
    }

    return (
        <Accordion>
            <Accordion.Title>
                Balance labels distribution <Accordion.Tag>{isEnabled ? 'On' : 'Off'}</Accordion.Tag>
            </Accordion.Title>
            <Accordion.Content>
                <LabelsDistribution labels={labels} />
                <Accordion.Divider marginY={'size-250'} />
                <Flex alignItems={'center'} gap={'size-300'}>
                    <label htmlFor={'balance-distribution'}>
                        Balance labels distribution <BalanceLabelsDistributionTooltip />
                    </label>
                    <Switch
                        isEmphasized
                        id={'balance-distribution'}
                        aria-label={'Balance labels distribution'}
                        isSelected={isEnabled}
                        onChange={setIsEnabled}
                    >
                        {isEnabled ? 'On' : 'Off'}
                    </Switch>
                </Flex>
            </Accordion.Content>
        </Accordion>
    );
};
