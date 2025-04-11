// INTEL CONFIDENTIAL
//
// Copyright (C) 2023 Intel Corporation
//
// This software and the related documents are Intel copyrighted materials, and your use of them is governed by
// the express license under which they were provided to you ("License"). Unless the License provides otherwise,
// you may not use, modify, copy, publish, distribute, disclose or transmit this software or the related documents
// without Intel's prior written permission.
//
// This software and the related documents are provided as is, with no express or implied warranties,
// other than those that are expressly stated in the License.

import { Flex, View } from '@adobe/react-spectrum';

import { useModels } from '../../../../core/models/hooks/use-models.hook';
import { useTests } from '../../../../core/tests/hooks/use-tests.hook';
import { filterOutUnsuccessfulTest } from '../../../../core/tests/services/utils';
import { TUTORIAL_CARD_KEYS } from '../../../../core/user-settings/dtos/user-settings.interface';
import { useProjectIdentifier } from '../../../../hooks/use-project-identifier/use-project-identifier';
import { LoadingIndicator } from '../../../../shared/components/loading/loading-indicator.component';
import { TutorialCardBuilder } from '../../../../shared/components/tutorial-card/tutorial-card-builder.component';
import { useRefetchTests } from './hooks/use-refetch-tests.hook';
import { RunTestButton } from './run-test-dialog/run-test-button.component';
import { TestsTable } from './tests-table.component';

export const Tests = (): JSX.Element => {
    const projectIdentifier = useProjectIdentifier();
    const { useTestsListQuery } = useTests();

    const { useProjectModelsQuery } = useModels();
    const projectModelsQuery = useProjectModelsQuery();
    const { data: modelsGroups = [] } = projectModelsQuery;
    const isLoadingModels = projectModelsQuery.isPending || projectModelsQuery.isLoading;

    const testsListsQuery = useTestsListQuery(projectIdentifier);
    const { data: tests = [], refetch, isLoading: areTestsLoading } = testsListsQuery;
    const isLoadingTests = testsListsQuery.isPending || testsListsQuery.isLoading;

    useRefetchTests(tests, async () => {
        await refetch();
    });

    const successfulTests = tests.filter(filterOutUnsuccessfulTest);

    if (areTestsLoading) {
        return <LoadingIndicator />;
    }

    return (
        <Flex direction={'column'} height={'100%'} gap={'size-200'}>
            <TutorialCardBuilder cardKey={TUTORIAL_CARD_KEYS.PROJECT_TESTS_TUTORIAL} />
            <Flex justifyContent={'end'}>
                <RunTestButton modelsGroups={modelsGroups} />
            </Flex>

            <View flex={1} UNSAFE_style={{ overflowY: 'auto' }}>
                <TestsTable tests={successfulTests} isLoading={isLoadingTests || isLoadingModels} />
            </View>
        </Flex>
    );
};
