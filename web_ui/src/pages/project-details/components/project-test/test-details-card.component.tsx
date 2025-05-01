// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { ReactNode } from 'react';

import { Grid, repeat, Text } from '@adobe/react-spectrum';
import { Heading } from '@react-spectrum/text';
import { CardContent } from '@shared/components/card-content/card-content.component';
import { DomainName } from '@shared/components/domain-name/domain-name.component';

import { DOMAIN } from '../../../../core/projects/core.interface';
import { formatTestDate, formatTestTime } from '../project-tests/utils';

import classes from './project-test.module.scss';

interface TestDetailsCardProps {
    modelName: string;
    version: number;
    testingSetName: string;
    creationDate: string;
    numberOfLabels: number;
    numberOfImages: number;
    numberOfFrames: number;
    taskName: DOMAIN;
}

export const TestDetailsCard = ({
    modelName,
    version,
    testingSetName,
    creationDate,
    numberOfLabels,
    numberOfImages,
    numberOfFrames,
    taskName,
}: TestDetailsCardProps): JSX.Element => {
    return (
        <CardContent title={'Details'} gridArea={'details'}>
            <Grid columns={repeat(2, '1fr')} height={'100%'} gap={'size-200'}>
                <Grid columns={['max-content', '1fr']} columnGap={'size-200'} rowGap={'size-100'}>
                    <Text>Task:</Text>
                    <TestDetailCardBoldItem id={'test-details-task-id'}>
                        <DomainName domain={taskName} />
                    </TestDetailCardBoldItem>
                    <Text>Model:</Text>
                    <Text>
                        <TestDetailCardBoldItem id={'test-details-model-name-id'}>{modelName} </TestDetailCardBoldItem>
                        <TestDetailCardItem id={'test-details-model-version-id'}>Version {version}</TestDetailCardItem>
                    </Text>
                    <Text>Testing set:</Text>
                    <TestDetailCardBoldItem>{testingSetName}</TestDetailCardBoldItem>
                </Grid>
                <Grid
                    columns={['max-content', '1fr']}
                    columnGap={'size-200'}
                    rowGap={'size-100'}
                    alignContent={'start'}
                >
                    <Text>Creation date:</Text>
                    <Text>
                        <TestDetailCardBoldItem>{formatTestDate(creationDate)}</TestDetailCardBoldItem>
                        {', '}
                        <TestDetailCardItem id={'test-details-creation-date-id'}>
                            {formatTestTime(creationDate)}
                        </TestDetailCardItem>
                    </Text>
                    <Text>Labels:</Text>
                    <TestDetailCardBoldItem id={'test-details-number-of-labels-id'}>
                        {numberOfLabels}
                    </TestDetailCardBoldItem>
                    <Text>Images / Frames:</Text>
                    <TestDetailCardBoldItem id={'test-details-images-frames-id'}>
                        {numberOfImages} / {numberOfFrames}
                    </TestDetailCardBoldItem>
                </Grid>
            </Grid>
        </CardContent>
    );
};

interface TestDetailCardBoldItemProps {
    id?: string;
    children: ReactNode;
}

const TestDetailCardBoldItem = ({ id, children }: TestDetailCardBoldItemProps) => {
    return (
        <Heading id={id} UNSAFE_className={classes.testDetailsCardBoldItem}>
            {children}
        </Heading>
    );
};

interface TestDetailCardItemProps {
    id?: string;
    children: ReactNode;
}

const TestDetailCardItem = ({ id, children }: TestDetailCardItemProps) => {
    return (
        <Text id={id} UNSAFE_className={classes.testDetailsCardItem}>
            {children}
        </Text>
    );
};
