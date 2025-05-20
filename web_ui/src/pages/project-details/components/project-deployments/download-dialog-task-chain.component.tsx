// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { useMemo, useState } from 'react';

import { Button, ButtonGroup, Content, Dialog, Divider, Flex, Heading } from '@geti/ui';
import { isEmpty } from 'lodash-es';

import { useCodeDeployment } from '../../../../core/code-deployment/hooks/use-code-deployment.hook';
import { useFeatureFlags } from '../../../../core/feature-flags/hooks/use-feature-flags.hook';
import { ModelsGroups } from '../../../../core/models/models.interface';
import { ProjectIdentifier } from '../../../../core/projects/core.interface';
import { Task } from '../../../../core/projects/task.interface';
import { TooltipWithDisableButton } from '../../../../shared/components/custom-tooltip/tooltip-with-disable-button';
import { getTaskModels } from '../../utils';
import { DeployModel, DeployModelByTask } from './interfaces';
import { ModelSelection } from './model-selection.component';
import { DEPLOYMENT_PACKAGE_TYPES, SelectDeploymentPackage } from './select-deployment-package.component';
import { TaskChainInfo } from './task-chain-info.component';
import { useSelectDeploymentOptions } from './use-select-deployment-options.hook';

import classes from './project-deployments.module.scss';

const DISABLED_BUTTON_TEXT = 'Please select an architecture, version and optimization type';
const DOWNLOAD = 'Download';
const NEXT = 'Next';
const BACK = 'Back';
const CANCEL = 'Cancel';

interface DownloadDialogTaskChainProps {
    close: () => void;
    modelsGroups: ModelsGroups[];
    tasks: Task[];
    projectIdentifier: ProjectIdentifier;
}

export const DownloadDialogTaskChain = ({
    close,
    modelsGroups,
    tasks,
    projectIdentifier,
}: DownloadDialogTaskChainProps): JSX.Element => {
    const [modelSelection, setModelSelection] = useState<DeployModelByTask>({});

    const {
        taskIndex,
        selectedTask,
        prevButtonEnabled,
        showNextButton,
        downloadEnabled,
        nextButtonEnabled,
        next,
        previous,
    } = useSelectDeploymentOptions({ modelSelection, tasks });

    const { FEATURE_FLAG_OVMS_DEPLOYMENT_PACKAGE } = useFeatureFlags();
    const { useDownloadDeploymentPackageMutation } = useCodeDeployment();
    const downloadDeploymentPackageMutation = useDownloadDeploymentPackageMutation();
    const [selectedDeploymentPackageType, setSelectedDeploymentPackageType] = useState<DEPLOYMENT_PACKAGE_TYPES>(
        DEPLOYMENT_PACKAGE_TYPES.CODE_DEPLOYMENT
    );

    const isDownloadButtonPending = downloadDeploymentPackageMutation.isPending;

    const models: ModelsGroups[] = useMemo(() => {
        return getTaskModels(modelsGroups, selectedTask.id);
    }, [modelsGroups, selectedTask]);

    if (isEmpty(models)) {
        return <></>;
    }

    const firstDeployModel: DeployModel = {
        modelGroupId: models[0].groupId,
        versionId: models[0].modelVersions[0].id,
        optimisationId: undefined,
        modelId: models[0].modelVersions[0].id,
    };

    const taskName = selectedTask.title.split(' ')[0];

    const handleSelectModel = (model: DeployModel): void => {
        setModelSelection({
            ...modelSelection,
            [selectedTask.id]: model,
        });
    };

    const handleDownload = () => {
        if (
            Object.values(modelSelection).some(
                (deployModel) => !deployModel.optimisationId || !deployModel.modelGroupId
            )
        ) {
            return;
        }

        downloadDeploymentPackageMutation.mutate(
            {
                projectIdentifier,
                body: {
                    models: Object.values(modelSelection).map((deployModel) => ({
                        modelId: deployModel.optimisationId as string,
                        modelGroupId: deployModel.modelGroupId,
                    })),
                    packageType:
                        selectedDeploymentPackageType === DEPLOYMENT_PACKAGE_TYPES.OVMS_DEPLOYMENT
                            ? 'ovms'
                            : 'geti_sdk',
                },
            },
            {
                onSuccess: close,
            }
        );
    };

    return (
        <Dialog UNSAFE_className={classes.dialog}>
            <Heading>Select the model for deployment</Heading>
            <Divider />

            <Content>
                <Flex direction={'column'} gap={'size-200'}>
                    <Flex direction={'column'} gap={'size-150'}>
                        {FEATURE_FLAG_OVMS_DEPLOYMENT_PACKAGE && (
                            <SelectDeploymentPackage
                                selectedDeploymentPackageType={selectedDeploymentPackageType}
                                onSelectDeploymentPackageType={setSelectedDeploymentPackageType}
                                isDisabled={taskIndex !== 0}
                            />
                        )}
                        <TaskChainInfo taskName={taskName} taskIndex={taskIndex} />
                    </Flex>

                    <Divider size={'S'} />

                    <ModelSelection
                        key={selectedTask.id}
                        models={models}
                        selectedModel={firstDeployModel}
                        selectModel={handleSelectModel}
                    />
                </Flex>
            </Content>

            <ButtonGroup UNSAFE_className={classes.taskChainButtonGroup}>
                <Button variant='secondary' onPress={close} id={'cancel-button-id'}>
                    {CANCEL}
                </Button>

                {prevButtonEnabled ? (
                    <Button variant='secondary' onPress={previous} id={'previous-button-id'}>
                        {BACK}
                    </Button>
                ) : null}

                {!showNextButton ? (
                    <TooltipWithDisableButton disabledTooltip={DISABLED_BUTTON_TEXT}>
                        <Button
                            UNSAFE_className={classes.taskChainButtonWithTooltip}
                            isPending={isDownloadButtonPending}
                            variant='accent'
                            onPress={handleDownload}
                            isDisabled={!downloadEnabled}
                            marginStart={'size-200'}
                            id={'download-button-id'}
                        >
                            {DOWNLOAD}
                        </Button>
                    </TooltipWithDisableButton>
                ) : (
                    <TooltipWithDisableButton disabledTooltip={DISABLED_BUTTON_TEXT}>
                        <Button
                            UNSAFE_className={classes.taskChainButtonWithTooltip}
                            variant='accent'
                            isDisabled={!nextButtonEnabled}
                            onPress={next}
                            id={'next-button-id'}
                        >
                            {NEXT}
                        </Button>
                    </TooltipWithDisableButton>
                )}
            </ButtonGroup>
        </Dialog>
    );
};
