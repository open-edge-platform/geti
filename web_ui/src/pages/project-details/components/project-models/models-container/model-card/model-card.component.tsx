// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { paths } from '@geti/core';
import { Flex, Heading, Tag, Text, View } from '@geti/ui';
import { Fps, Image, Tag as TagIcon } from '@geti/ui/icons';
import { clsx } from 'clsx';
import { usePress } from 'react-aria';
import { useNavigate } from 'react-router-dom';

import { isExclusive } from '../../../../../../core/labels/utils';
import { ModelFormat } from '../../../../../../core/models/dtos/model-details.interface';
import { useModels } from '../../../../../../core/models/hooks/use-models.hook';
import { isAnomalyDomain } from '../../../../../../core/projects/domains';
import { useModelIdentifier } from '../../../../../../hooks/use-model-identifier/use-model-identifier.hook';
import { formatDate, isNonEmptyString } from '../../../../../../shared/utils';
import { useProject } from '../../../../providers/project-provider/project-provider.component';
import { isModelDeleted } from '../../../../utils';
import { ActiveModelTag } from './active-model-tag.component';
import { CountWithIcon } from './count-with-icon.component';
import { ModelCardMenu } from './model-card-menu.component';
import { ModelCardProps } from './model-card.interface';
import { ModelInfoFields } from './model-info-fields.component';
import { ModelPerformance } from './model-performance.component';

import classes from './model-card.module.scss';

export const ModelCard = ({
    model,
    taskId,
    isLatestModel,
    modelTemplateId,
    isMenuOptionsDisabled,
    complexity,
}: ModelCardProps): JSX.Element => {
    const { id, version, performance, creationDate, isActiveModel, groupId, groupName, isLabelSchemaUpToDate } = model;

    const navigate = useNavigate();
    const { project } = useProject();
    const { useModelQuery } = useModels();
    const projectIdentifier = useModelIdentifier();
    const { data: modelDetails, isLoading: isLoadingModelDetails } = useModelQuery({
        ...projectIdentifier,
        groupId,
        modelId: id,
    });

    const modelUrl = paths.project.models.model.index({ ...projectIdentifier, groupId, modelId: id });
    const { pressProps } = usePress({ onPress: () => navigate(modelUrl) });

    const genericId = `${groupId}-${id}`;
    const isAnomalyProject = project.domains.some(isAnomalyDomain);
    const labels = (modelDetails?.labels ?? []).filter((label) => isAnomalyProject || !isExclusive(label));

    const numberOfLabels = labels.length;
    const numberOfImages = modelDetails?.trainedModel.numberOfImages ?? 0;
    const numberOfFrames = modelDetails?.trainedModel.numberOfFrames ?? 0;
    const totalDiskSize = isNonEmptyString(modelDetails?.trainedModel.totalDiskSize)
        ? modelDetails?.trainedModel.totalDiskSize
        : '0';

    const baseModel = modelDetails?.optimizedModels.find((optimizedModel) => {
        return (
            optimizedModel.hasExplainableAI === false &&
            optimizedModel.modelFormat === ModelFormat.OpenVINO &&
            optimizedModel.precision.some((precision) => precision === 'FP32')
        );
    });

    return (
        <div {...pressProps} className={classes.modelCard} aria-label={`${groupName} version ${version}`}>
            <View
                borderWidth={'thin'}
                borderRadius={'small'}
                borderColor={'gray-75'}
                data-testid={`model-card-${id}`}
                UNSAFE_className={clsx({
                    [classes.modelDeleted]: isModelDeleted(model),
                    [classes.modelCardNotTraining]: true,
                })}
            >
                <Flex alignItems={'center'} gap={'size-200'}>
                    <ModelPerformance
                        genericId={genericId}
                        performance={performance}
                        isDisabled={isModelDeleted(model)}
                        isModelTraining={false}
                    />
                    <Flex direction={'column'} width={'100%'} gap='size-100'>
                        <Flex alignItems={'center'} justifyContent={'space-between'}>
                            <Text UNSAFE_className={classes.modelInfo} data-testid={'trained-model-date-id'}>
                                Trained: {formatDate(creationDate, 'DD MMM YYYY, hh:mm A')}
                            </Text>

                            <Flex alignItems={'center'} gap={'size-225'} height={'size-225'}>
                                <CountWithIcon
                                    id={genericId}
                                    count={numberOfLabels}
                                    text={'label'}
                                    icon={<TagIcon />}
                                />
                                <CountWithIcon id={genericId} count={numberOfImages} text={'image'} icon={<Image />} />
                                <CountWithIcon id={genericId} count={numberOfFrames} text={'frame'} icon={<Fps />} />
                                <ModelCardMenu
                                    model={model}
                                    taskId={taskId}
                                    isLatestModel={isLatestModel}
                                    modelTemplateId={modelTemplateId}
                                    projectIdentifier={projectIdentifier}
                                    isMenuOptionsDisabled={isMenuOptionsDisabled}
                                />
                            </Flex>
                        </Flex>
                        <Flex alignItems={'center'} gap='size-150'>
                            <Heading id={`version-${genericId}-id`} data-testid={`version-${genericId}-id`} margin={0}>
                                Version {version}
                            </Heading>
                            <Flex gap={'size-200'} height={'size-200'}>
                                {isActiveModel && <ActiveModelTag id={genericId} />}
                                {isModelDeleted(model) && (
                                    <Tag
                                        id={`model-deleted-${genericId}`}
                                        text={'Files deleted'}
                                        withDot={false}
                                        className={classes.deletedModelTag}
                                    />
                                )}
                                {!isLabelSchemaUpToDate && (
                                    <Tag
                                        id={`labels-out-of-date-${genericId}-id`}
                                        text={'Labels out-of-date'}
                                        withDot={false}
                                        className={classes.labelsOutOfDateTag}
                                    />
                                )}
                            </Flex>
                        </Flex>
                        <Text
                            id={`model-info-${genericId}-id`}
                            data-testid={`model-info-${genericId}-id`}
                            UNSAFE_className={classes.modelInfo}
                        >
                            <ModelInfoFields
                                modelSize={baseModel && !isModelDeleted(model) ? baseModel.modelSize : undefined}
                                totalDiskSize={
                                    !isLoadingModelDetails && !isModelDeleted(model) ? totalDiskSize : undefined
                                }
                                complexity={complexity}
                                isModelTraining={false}
                            />
                        </Text>
                    </Flex>
                </Flex>
            </View>
        </div>
    );
};
