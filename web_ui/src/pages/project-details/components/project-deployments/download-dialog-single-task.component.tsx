// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { useState } from 'react';

import { Button, ButtonGroup, Content, Dialog, Divider, Flex, Heading } from '@geti/ui';

import { useCodeDeployment } from '../../../../core/code-deployment/hooks/use-code-deployment.hook';
import { useFeatureFlags } from '../../../../core/feature-flags/hooks/use-feature-flags.hook';
import { ModelsGroups } from '../../../../core/models/models.interface';
import { ProjectIdentifier } from '../../../../core/projects/core.interface';
import { Task } from '../../../../core/projects/task.interface';
import { TooltipWithDisableButton } from '../../../../shared/components/custom-tooltip/tooltip-with-disable-button';
import { DeployModel } from './interfaces';
import { ModelSelection } from './model-selection.component';
import { DEPLOYMENT_PACKAGE_TYPES, SelectDeploymentPackage } from './select-deployment-package.component';

const DISABLED_DOWNLOAD_BUTTON_TEXT = 'Please select an architecture, version and optimization type';
const DOWNLOAD = 'Download';

interface DownloadDialogSingleTaskProps {
    close: () => void;
    modelsGroups: ModelsGroups[];
    task: Task;
    projectIdentifier: ProjectIdentifier;
}

export const DownloadDialogSingleTask = ({
    close,
    modelsGroups,
    task,
    projectIdentifier,
}: DownloadDialogSingleTaskProps): JSX.Element => {
    const firstDeployModel: DeployModel = {
        modelGroupId: modelsGroups[0].groupId,
        modelId: modelsGroups[0].modelVersions[0].id,
        optimisationId: undefined,
        versionId: modelsGroups[0].modelVersions[0].id,
    };
    const { FEATURE_FLAG_OVMS_DEPLOYMENT_PACKAGE } = useFeatureFlags();
    const { useDownloadDeploymentPackageMutation } = useCodeDeployment();
    const downloadDeploymentPackageMutation = useDownloadDeploymentPackageMutation();

    const [selectedModel, setSelectedModel] = useState<DeployModel>(firstDeployModel);
    const [selectedDeploymentPackageType, setSelectedDeploymentPackageType] = useState<DEPLOYMENT_PACKAGE_TYPES>(
        DEPLOYMENT_PACKAGE_TYPES.CODE_DEPLOYMENT
    );

    const isDownloadButtonDisabled = !selectedModel.optimisationId;
    const isDownloadButtonPending = downloadDeploymentPackageMutation.isPending;

    const handleSelectModel = (model: DeployModel): void => {
        setSelectedModel(model);
    };

    const handleDownload = () => {
        if (!selectedModel.optimisationId || !selectedModel.modelGroupId) {
            return;
        }
        downloadDeploymentPackageMutation.mutate(
            {
                projectIdentifier,
                body: {
                    models: [{ modelId: selectedModel.optimisationId, modelGroupId: selectedModel.modelGroupId }],
                    packageType:
                        selectedDeploymentPackageType === DEPLOYMENT_PACKAGE_TYPES.OVMS_DEPLOYMENT
                            ? 'ovms'
                            : 'geti_sdk',
                },
            },
            { onSuccess: close }
        );
    };

    return (
        <Dialog>
            <Heading>Select the model for deployment</Heading>
            <Divider />

            <Content>
                <Flex direction={'column'} gap={'size-150'}>
                    {FEATURE_FLAG_OVMS_DEPLOYMENT_PACKAGE && (
                        <SelectDeploymentPackage
                            onSelectDeploymentPackageType={setSelectedDeploymentPackageType}
                            selectedDeploymentPackageType={selectedDeploymentPackageType}
                        />
                    )}
                    <ModelSelection
                        key={task.id}
                        models={modelsGroups}
                        selectedModel={firstDeployModel}
                        selectModel={handleSelectModel}
                    />
                </Flex>
            </Content>

            <ButtonGroup>
                <Button variant='secondary' onPress={close} id={'cancel-button-id'}>
                    Cancel
                </Button>

                <TooltipWithDisableButton disabledTooltip={DISABLED_DOWNLOAD_BUTTON_TEXT}>
                    <Button
                        isPending={isDownloadButtonPending}
                        variant='accent'
                        onPress={handleDownload}
                        isDisabled={isDownloadButtonDisabled}
                        marginStart={'size-200'}
                        id={'download-button-id'}
                    >
                        {DOWNLOAD}
                    </Button>
                </TooltipWithDisableButton>
            </ButtonGroup>
        </Dialog>
    );
};
