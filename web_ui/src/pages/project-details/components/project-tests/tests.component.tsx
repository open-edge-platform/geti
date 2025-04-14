// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

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
