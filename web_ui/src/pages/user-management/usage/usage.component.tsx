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

import { Flex, Heading, Text } from '@adobe/react-spectrum';
import { DateValue, getLocalTimeZone, parseDate, today } from '@internationalized/date';
import dayjs from 'dayjs';

import { MonthPicker } from '../../../shared/components/month-picker/month-picker.component';
import { CreditConsumptionCard } from './credit-consumption-card.component';
import { CreditConsumptionRecords } from './credit-consumption-records.component';
import { MonthlyCreditConsumptionCard } from './monthly-credit-consumption-card.component';
import { ProjectsCreditConsumptionCard } from './projects-credit-consumption-card.component';
import { TimeCreditConsumptionCard } from './time-credit-consumption-card.component';
import { UsageCreditAccountsCard } from './usage-credit-accounts-card.component';

import classes from './usage.module.scss';

const MIN_DATE = parseDate('2024-01-01');
const MAX_DATE = today(getLocalTimeZone());

export const Usage = (): JSX.Element => {
    const timeZone = getLocalTimeZone();
    const [projectsConsumptionDate, setProjectsConsumptionDate] = useState<DateValue>(today(timeZone).set({ day: 1 }));
    const [timeConsumptionDate, setTimeConsumptionDate] = useState<DateValue>(today(timeZone).set({ day: 1 }));

    return (
        <>
            <Flex gap='size-600'>
                <CreditConsumptionCard flex='1' />
                <UsageCreditAccountsCard flex='2' />
            </Flex>
            <Heading level={2} marginTop={'size-600'} UNSAFE_className={classes.withBottomBorder}>
                Monthly credit consumption
            </Heading>
            <MonthlyCreditConsumptionCard
                marginTop={'size-250'}
                UNSAFE_className={classes.monthlyCreditConsumptionCard}
            />
            <Heading level={2} marginTop={'size-600'} marginBottom={'size-50'}>
                Credit consumption by projects
            </Heading>
            <Flex justifyContent={'space-between'} alignItems={'baseline'} UNSAFE_className={classes.withBottomBorder}>
                <Text data-testid='projects-credit-consumption-month-picker-value-text'>
                    {dayjs(projectsConsumptionDate.toDate(timeZone)).format('MMMM / YYYY')}
                </Text>
                <MonthPicker
                    value={projectsConsumptionDate}
                    onChange={setProjectsConsumptionDate}
                    minValue={MIN_DATE}
                    maxValue={MAX_DATE}
                    isButtonQuiet
                />
            </Flex>
            <ProjectsCreditConsumptionCard
                fromDate={projectsConsumptionDate.set({ day: 1 }).toDate(timeZone)}
                toDate={projectsConsumptionDate.add({ months: 1 }).set({ day: 1 }).toDate(timeZone)}
                marginTop={'size-250'}
            />
            <Heading level={2} marginTop={'size-600'} marginBottom={'size-50'}>
                Credit consumption by time
            </Heading>
            <Flex justifyContent={'space-between'} alignItems={'baseline'} UNSAFE_className={classes.withBottomBorder}>
                <Text>{dayjs(timeConsumptionDate.toDate(timeZone)).format('MMMM / YYYY')}</Text>
                <MonthPicker
                    value={timeConsumptionDate}
                    onChange={setTimeConsumptionDate}
                    minValue={MIN_DATE}
                    maxValue={MAX_DATE}
                    isButtonQuiet
                />
            </Flex>
            <TimeCreditConsumptionCard
                fromDate={timeConsumptionDate.set({ day: 1 }).toDate(timeZone)}
                toDate={timeConsumptionDate.add({ months: 1 }).set({ day: 1 }).toDate(timeZone)}
                marginTop={'size-250'}
            />

            <CreditConsumptionRecords />
        </>
    );
};
