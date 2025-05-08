// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { Divider, Flex, Text } from '@adobe/react-spectrum';
import { isEmpty } from 'lodash-es';

import classes from './anomaly-media-header-information.module.scss';

interface AnomalyMediaHeaderInformationProps {
    headerText: string;
    countElements: string | undefined;
    description: string;
}

export const AnomalyMediaHeaderInformation = ({
    countElements,
    description,
    headerText,
}: AnomalyMediaHeaderInformationProps): JSX.Element => {
    return (
        <Flex direction={'column'} flex={1}>
            <Flex gap='size-100' alignItems='center'>
                <Text UNSAFE_className={classes.header}>{headerText}</Text>

                {!isEmpty(countElements) && (
                    <>
                        <Divider orientation='vertical' size='S' />
                        <Text id='count-message-id' data-testid='count-message-id'>
                            {countElements}
                        </Text>
                    </>
                )}
            </Flex>
            <Text UNSAFE_className={classes.description}>{description}</Text>
        </Flex>
    );
};
