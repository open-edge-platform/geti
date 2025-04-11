// INTEL CONFIDENTIAL
//
// Copyright (C) 2021 Intel Corporation
//
// This software and the related documents are Intel copyrighted materials, and your use of them is governed by
// the express license under which they were provided to you ("License"). Unless the License provides otherwise,
// you may not use, modify, copy, publish, distribute, disclose or transmit this software or the related documents
// without Intel's prior written permission.
//
// This software and the related documents are provided as is, with no express or implied warranties,
// other than those that are expressly stated in the License.

import { Flex, Link, Text, View } from '@adobe/react-spectrum';
import { Link as RouterLink } from 'react-router-dom';

import { InfoOutline } from '../../../../../assets/icons';
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
