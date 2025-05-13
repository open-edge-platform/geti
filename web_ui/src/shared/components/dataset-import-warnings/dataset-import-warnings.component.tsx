// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { Divider, Flex, Heading, Text, View } from '@adobe/react-spectrum';
import Alert from '@spectrum-icons/workflow/Alert';
import { capitalize } from 'lodash-es';

import { Image } from '../../../assets/icons';
import { DATASET_IMPORT_WARNING_TYPE } from '../../../core/datasets/dataset.enum';
import { DatasetImportWarning } from '../../../core/datasets/dataset.interface';

import classes from './dataset-import-warnings.module.scss';

interface DatasetImportWarningsProps {
    warnings: DatasetImportWarning[];
}

interface DatasetImportWarningItemProps {
    warning: DatasetImportWarning;
}

const DatasetImportWarningItem = ({ warning }: DatasetImportWarningItemProps): JSX.Element => {
    const { type, name, description, affectedImages, resolveStrategy } = warning;

    return (
        <div aria-label='dataset-import-warnings'>
            <View height='size-1200' backgroundColor='gray-100' padding='size-200'>
                <Flex height='100%' direction='column' gap='size-100'>
                    <Flex alignItems='start' justifyContent='space-between'>
                        <Flex flex={3} alignItems='center' gap='size-200'>
                            <Alert
                                size='S'
                                marginStart='size-50'
                                data-testid='alert-icon'
                                UNSAFE_className={
                                    type === DATASET_IMPORT_WARNING_TYPE.ERROR ? classes.negative : classes.warning
                                }
                            />
                            <Text UNSAFE_className={classes.warningName}>
                                {type === DATASET_IMPORT_WARNING_TYPE.ERROR
                                    ? capitalize(DATASET_IMPORT_WARNING_TYPE.ERROR)
                                    : capitalize(DATASET_IMPORT_WARNING_TYPE.WARNING)}
                                {''} - {name}
                            </Text>
                        </Flex>
                        {affectedImages !== undefined ? (
                            <Flex flex={1} alignItems='center' justifyContent='end' gap='size-50'>
                                <Image />
                                <Text>{`${affectedImages} affected image${affectedImages > 1 ? 's' : ''}`}</Text>
                            </Flex>
                        ) : null}
                    </Flex>
                    <Flex alignItems='center' justifyContent='space-between'>
                        <Text UNSAFE_className={classes.warningDescription}>{description}</Text>
                    </Flex>
                    {resolveStrategy && <Divider size='S' marginY='size-50' />}
                    <Flex marginStart='size-500' data-testid='resolve-strategy-container'>
                        {resolveStrategy}
                    </Flex>
                </Flex>
            </View>
        </div>
    );
};

export const DatasetImportWarnings = ({ warnings }: DatasetImportWarningsProps): JSX.Element => {
    return (
        <Flex direction='column' height='100%' gap='size-250'>
            <Heading marginBottom={0} level={3} id='dataset-import-warnings-header'>
                Detected issues in the dataset
            </Heading>
            <Flex direction='column' gap='size-200' UNSAFE_className={classes.warnings}>
                {warnings.map((warning: DatasetImportWarning, idx: number) => (
                    <DatasetImportWarningItem key={`${warning.name}-${idx}`} warning={warning} />
                ))}
            </Flex>
        </Flex>
    );
};
