// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { Flex, Link, Text, View } from '@geti/ui';
import { InfoOutline } from '@geti/ui/icons';
import { Link as RouterLink } from 'react-router-dom';

import { paths } from '../../../../../core/services/routes';
import { useDataset } from '../../../providers/dataset-provider/dataset-provider.component';

interface EmptyDataSetProps {
    isActiveMode?: boolean;
}

export const EmptyDataSet = ({ isActiveMode = false }: EmptyDataSetProps): JSX.Element => {
    const { datasetIdentifier } = useDataset();

    return (
        <View marginTop='size-200'>
            <Flex>
                <View paddingX='size-100' paddingTop={'size-25'}>
                    <InfoOutline width={16} height={16} />
                </View>
                <Flex direction='column'>
                    <Text>{isActiveMode ? 'Active set' : 'Dataset'} is empty</Text>

                    <Text>
                        {' '}
                        Please select a different dataset or{' '}
                        <Link variant='overBackground'>
                            <RouterLink to={paths.project.dataset.index(datasetIdentifier)} viewTransition>
                                upload new media items
                            </RouterLink>
                        </Link>{' '}
                        to start annotating.
                    </Text>
                </Flex>
            </Flex>
        </View>
    );
};
