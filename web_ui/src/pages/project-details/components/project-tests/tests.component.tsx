// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { Flex, Loading, View } from '@geti/ui';
import { isEmpty } from 'lodash-es';

import { useModels } from '../../../../core/models/hooks/use-models.hook';
import { JobInfoStatus } from '../../../../core/tests/dtos/tests.interface';
import { useTests } from '../../../../core/tests/hooks/use-tests.hook';
import { filterOutUnsuccessfulTest } from '../../../../core/tests/services/utils';
import { TUTORIAL_CARD_KEYS } from '../../../../core/user-settings/dtos/user-settings.interface';
import { useProjectIdentifier } from '../../../../hooks/use-project-identifier/use-project-identifier';
import { TutorialCardBuilder } from '../../../../shared/components/tutorial-card/tutorial-card-builder.component';
import { RunTestButton } from './run-test-dialog/run-test-button.component';
import { TestsTable } from './tests-table.component';

const TIME_TO_REFETCH_TESTS = 2000;

export const Tests = (): JSX.Element => {
    const projectIdentifier = useProjectIdentifier();
    const { useTestsListQuery } = useTests();

    const { useProjectModelsQuery } = useModels();
    const projectModelsQuery = useProjectModelsQuery();
    const { data: modelsGroups = [] } = projectModelsQuery;
    const isLoadingModels = projectModelsQuery.isPending || projectModelsQuery.isLoading;

    const {
        data: tests = [],
        isLoading: areTestsLoading,
        isPending: areTestsPending,
    } = useTestsListQuery(projectIdentifier, {
        refetchInterval: (query) => {
            const data = query.state.data;

            const shouldRefetch =
                data !== undefined &&
                !isEmpty(data) &&
                !data.every(
                    ({ jobInfo }) => jobInfo.status === JobInfoStatus.DONE || jobInfo.status === JobInfoStatus.ERROR
                );

            return shouldRefetch ? TIME_TO_REFETCH_TESTS : false;
        },
    });
    const isLoadingTests = areTestsPending || areTestsLoading;

    const successfulTests = tests.filter(filterOutUnsuccessfulTest);

    if (areTestsLoading) {
        return <Loading />;
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
