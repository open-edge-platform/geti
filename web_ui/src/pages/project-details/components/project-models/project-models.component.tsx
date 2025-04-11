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

import { Flex, View } from '@adobe/react-spectrum';

import { NoTrainedModels } from '../../../../assets/images';
import { useModels } from '../../../../core/models/hooks/use-models.hook';
import { TUTORIAL_CARD_KEYS } from '../../../../core/user-settings/dtos/user-settings.interface';
import { EmptyData } from '../../../../shared/components/empty-data/empty-data.component';
import { Loading } from '../../../../shared/components/loading/loading.component';
import { PageLayout } from '../../../../shared/components/page-layout/page-layout.component';
import { TutorialCardBuilder } from '../../../../shared/components/tutorial-card/tutorial-card-builder.component';
import { isNonEmptyArray, isNotCropTask } from '../../../../shared/utils';
import { useTasksWithSupportedAlgorithms } from '../../hooks/use-tasks-with-supported-algorithms';
import { useProject } from '../../providers/project-provider/project-provider.component';
import { EmptyDataTrainingProgress } from './empty-data-training-progress.componen';
import { useIsTraining } from './hooks/use-is-training.hook';
import { ModelsGroupsPerTasks } from './models-groups-per-tasks.component';
import { ModelsGroupsSingleTask } from './models-groups-single-task.component';
import { ReconfigureModels } from './reconfigure-models/reconfigure-models.component';
import { TrainModel } from './train-model-dialog/train-model.component';
import { addAlgorithmDetails } from './utils';

export const ProjectModels = (): JSX.Element => {
    const { useProjectModelsQuery } = useModels();
    const { tasksWithSupportedAlgorithms } = useTasksWithSupportedAlgorithms();
    const isTraining = useIsTraining();

    const {
        project: { tasks },
        isTaskChainProject,
    } = useProject();

    const { data = [], isLoading, isInitialLoading } = useProjectModelsQuery();

    const formattedModelsGroups = data.map(addAlgorithmDetails(tasksWithSupportedAlgorithms));

    const isLoadingModels = isLoading || isInitialLoading;

    return (
        <>
            <PageLayout
                breadcrumbs={[{ id: 'models-id', breadcrumb: 'Models' }]}
                header={
                    <Flex alignItems={'center'} gap={'size-150'}>
                        <ReconfigureModels />
                        {!isLoadingModels && <TrainModel models={formattedModelsGroups} />}
                    </Flex>
                }
            >
                {isLoadingModels ? (
                    <Loading />
                ) : isNonEmptyArray(data) ? (
                    <View height={'100%'} marginTop={'size-50'}>
                        {isTaskChainProject ? (
                            <ModelsGroupsPerTasks modelsGroups={formattedModelsGroups} tasks={tasks} />
                        ) : (
                            <ModelsGroupsSingleTask modelsGroups={formattedModelsGroups} />
                        )}
                    </View>
                ) : isTraining ? (
                    <EmptyDataTrainingProgress isTaskChain={isTaskChainProject} tasks={tasks.filter(isNotCropTask)} />
                ) : (
                    <>
                        <TutorialCardBuilder cardKey={TUTORIAL_CARD_KEYS.PROJECT_MODEL_TUTORIAL} />
                        <EmptyData
                            beforeText={<NoTrainedModels />}
                            title={'No trained models'}
                            text={'Upload media and annotate to train a new model'}
                        />
                    </>
                )}
            </PageLayout>
        </>
    );
};
