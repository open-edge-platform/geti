// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { ReactElement } from 'react';

import {
    ActionButton,
    dimensionValue,
    Item,
    LoadingIndicator,
    Menu,
    MenuTrigger,
    PressableElement,
    Text,
    Tooltip,
    TooltipTrigger,
    View,
} from '@geti/ui';
import { useOverlayTriggerState } from '@react-stately/overlays';
import { isAxiosError } from 'axios';
import { isEqual, isFunction, isNil } from 'lodash-es';

import { ExclamationCircleOutlined, MoreMenu } from '../../../../../../assets/icons';
import { isVisualPromptModel } from '../../../../../../core/annotations/services/visual-prompt-service';
import { useCreditsQueries } from '../../../../../../core/credits/hooks/use-credits-api.hook';
import { useFeatureFlags } from '../../../../../../core/feature-flags/hooks/use-feature-flags.hook';
import { useModels } from '../../../../../../core/models/hooks/use-models.hook';
import { ModelIdentifier } from '../../../../../../core/models/models.interface';
import { NOTIFICATION_TYPE } from '../../../../../../notification/notification-toast/notification-type.enum';
import { useNotification } from '../../../../../../notification/notification.component';
import { formatDate } from '../../../../../../shared/utils';
import { useTotalCreditPrice } from '../../../../hooks/use-credits-to-consume.hook';
import { isModelDeleted } from '../../../../utils';
import { NotEnoughCreditsDialog } from '../../../common/not-enough-credits-dialog/not-enough-credits-dialog.component';
import { RunTestDialog } from '../../../project-tests/run-test-dialog/run-test-dialog.component';
import { getTrainingBodyDTO } from '../../legacy-train-model-dialog/utils';
import { ActivateModelDialog } from './activate-model-dialog.component';
import { DeleteModelDialog } from './delete-model-dialog.component';
import { ModelVersion } from './model-card.interface';
import { ACTIVATED_MODEL_MESSAGE } from './utils';

interface ModelCardMenuProps {
    model: ModelVersion;
    taskId: string;
    modelTemplateId: string;
    isLatestModel: boolean;
    isMenuOptionsDisabled: boolean;
    projectIdentifier: ModelIdentifier;
}
enum ModelCardMenuItems {
    Retrain = 'Retrain',
    Delete = 'Delete',
    RunTests = 'Run tests',
    SetActiveModel = 'Set as active model',
}

interface MenuOption {
    key: ModelCardMenuItems;
    id: string;
    tooltip: string;
    icon?: ReactElement;
    action: () => void;
    disabled?: boolean;
}

export const ModelCardMenu = ({
    model,
    taskId,
    isLatestModel,
    modelTemplateId,
    projectIdentifier,
    isMenuOptionsDisabled,
}: ModelCardMenuProps): JSX.Element => {
    const { addNotification } = useNotification();
    const { useGetOrganizationBalanceQuery } = useCreditsQueries();
    const { FEATURE_FLAG_CREDIT_SYSTEM } = useFeatureFlags();
    const { getCreditPrice, isLoading: isCreditsToConsumeLoading } = useTotalCreditPrice();
    const { data: balance, isLoading: isBalanceLoading } = useGetOrganizationBalanceQuery(
        { organizationId: projectIdentifier.organizationId },
        { enabled: FEATURE_FLAG_CREDIT_SYSTEM }
    );

    const { useTrainModelMutation, useActivateModelMutation } = useModels();
    const trainModel = useTrainModelMutation();
    const activateModel = useActivateModelMutation();
    const isActiveModelLoading = activateModel.isPending;

    const modelName = `${model.templateName} (${model.groupName})`;

    const { totalCreditsToConsume } = getCreditPrice(taskId);
    const runTestDialogState = useOverlayTriggerState({});
    const deleteDialogState = useOverlayTriggerState({});
    const activateModelDialogState = useOverlayTriggerState({});
    const notEnoughCreditsDialogState = useOverlayTriggerState({});

    const isNotEnoughCreditsToTrain =
        FEATURE_FLAG_CREDIT_SYSTEM &&
        !isNil(balance) &&
        !isNil(totalCreditsToConsume) &&
        totalCreditsToConsume > balance?.available;

    const handleRetrain = (): void => {
        if (isNotEnoughCreditsToTrain) {
            notEnoughCreditsDialogState.open();
            return;
        }
        trainModel.mutate({
            projectIdentifier,
            body: getTrainingBodyDTO({
                taskId,
                modelTemplateId,
                configParameters: undefined,
                trainFromScratch: false,
                isReshufflingSubsetsEnabled: false,
            }),
        });
    };

    const handleActivateModel = async (callback?: () => void) => {
        if (isNotEnoughCreditsToTrain && isFunction(callback)) {
            notEnoughCreditsDialogState.open();
            return;
        }
        try {
            await activateModel.mutateAsync(
                { ...projectIdentifier, groupId: model.groupId },
                {
                    onSuccess: () => {
                        addNotification({
                            message: ACTIVATED_MODEL_MESSAGE(modelName, model.version),
                            type: NOTIFICATION_TYPE.INFO,
                        });

                        isFunction(callback) && callback();

                        activateModelDialogState.close();
                    },
                }
            );
        } catch (error: unknown) {
            if (isAxiosError(error)) {
                addNotification({ message: error.message, type: NOTIFICATION_TYPE.ERROR });
            }
        }
    };

    const handleActivateModelOption = () =>
        model.isLabelSchemaUpToDate ? handleActivateModel() : activateModelDialogState.open();

    const getMenuOptions = () => {
        const menuOptions: MenuOption[] = [
            { key: ModelCardMenuItems.RunTests, id: 'run-tests-id', tooltip: '', action: runTestDialogState.open },
        ];

        const isPromptModel = isVisualPromptModel(model);

        if ((isLatestModel && model.isActiveModel) || isPromptModel) {
            menuOptions.unshift({
                key: ModelCardMenuItems.Retrain,
                id: 'retrain-id',
                tooltip: '',
                action: handleRetrain,
                disabled:
                    (FEATURE_FLAG_CREDIT_SYSTEM && (isCreditsToConsumeLoading || isBalanceLoading)) || isPromptModel,
            });
        }

        if (isLatestModel && !model.isActiveModel) {
            menuOptions.unshift({
                key: ModelCardMenuItems.SetActiveModel,
                id: 'set-as-active-model-id',
                tooltip: '',
                action: handleActivateModelOption,
                disabled: isPromptModel,
            });
        }

        if (!isLatestModel && !model.isActiveModel && !isModelDeleted(model)) {
            menuOptions.push({
                key: ModelCardMenuItems.Delete,
                id: 'archive-model-id',
                icon: <ExclamationCircleOutlined />,
                tooltip: 'Deleting unused model or old model versions will free up storage space',
                action: deleteDialogState.open,
                disabled: isPromptModel,
            });
        }

        return menuOptions;
    };

    if (isModelDeleted(model)) {
        return <View width={'size-400'}></View>;
    }

    const menuOptions = getMenuOptions();

    return isActiveModelLoading ? (
        <LoadingIndicator size='S' />
    ) : (
        <>
            <MenuTrigger>
                <ActionButton
                    isQuiet
                    id={'model-action-menu'}
                    aria-label={'Model action menu'}
                    isDisabled={isMenuOptionsDisabled}
                >
                    <MoreMenu />
                </ActionButton>
                <Menu
                    onAction={(key) => {
                        const { action } = menuOptions.find((option) => isEqual(option.key, key)) ?? {};

                        isFunction(action) && action();
                    }}
                    disabledKeys={menuOptions.filter(({ disabled }) => disabled).map(({ key }) => key)}
                >
                    {menuOptions.map(({ id, key, tooltip, icon }) => (
                        <Item key={key}>
                            {!tooltip ? (
                                <Text id={id}>{key}</Text>
                            ) : (
                                <TooltipTrigger placement={'bottom'}>
                                    <PressableElement
                                        id={id}
                                        gridRow={'2'}
                                        gridColumn={'3'}
                                        UNSAFE_style={{
                                            display: 'flex',
                                            alignItems: 'center',
                                            gap: dimensionValue('size-50'),
                                        }}
                                    >
                                        {icon}
                                        {key}
                                    </PressableElement>
                                    <Tooltip>{tooltip}</Tooltip>
                                </TooltipTrigger>
                            )}
                        </Item>
                    ))}
                </Menu>
            </MenuTrigger>

            <DeleteModelDialog
                modelId={model.id}
                version={model.version}
                groupId={model.groupId}
                modelName={model.groupName}
                overlayState={deleteDialogState}
            />

            <RunTestDialog
                preselectedModel={{ taskId, ...model }}
                handleClose={runTestDialogState.close}
                isOpen={runTestDialogState.isOpen}
            />

            <ActivateModelDialog
                isOpen={activateModelDialogState.isOpen}
                modelName={modelName}
                modelVersion={model.version}
                createdAt={formatDate(model.creationDate, 'DD MMMM YYYY, hh:mm A')}
                handleDismiss={activateModelDialogState.close}
                handleActivateModel={handleActivateModel}
                handleActivateAndRetrainModel={() => handleActivateModel(handleRetrain)}
            />

            {!isNil(balance) && !isNil(totalCreditsToConsume) && (
                <NotEnoughCreditsDialog
                    isOpen={notEnoughCreditsDialogState.isOpen}
                    onClose={notEnoughCreditsDialogState.close}
                    creditsToConsume={totalCreditsToConsume}
                    creditsAvailable={balance.available}
                    message={{
                        header: 'Needed to retrain model:',
                        body: 'You don’t have enough credits to retrain model. Get more credits or upgrade your plan.',
                    }}
                />
            )}
        </>
    );
};
