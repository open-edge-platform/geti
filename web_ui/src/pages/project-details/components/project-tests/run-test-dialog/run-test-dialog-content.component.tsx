// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { useEffect } from 'react';

import { paths } from '@geti/core/src/services/routes';
import {
    Button,
    ButtonGroup,
    Content,
    Dialog,
    Divider,
    Flex,
    Heading,
    Item,
    Picker,
    Text,
    TextField,
    View,
} from '@geti/ui';
import { Link } from 'react-router-dom';

import { isVisualPromptModel } from '../../../../../core/annotations/services/visual-prompt-service';
import { useProjectIdentifier } from '../../../../../hooks/use-project-identifier/use-project-identifier';
import { WarningMessage } from '../../../../../shared/components/warning-message/warning-message.component';
import {
    DEFAULT_DATASET_MESSAGE,
    isModelDeleted,
    METRIC_ITEMS,
    NO_MODELS_MESSAGE,
    TESTING_SET_WAS_TESTED_WITH_THIS_CONFIGURATION_MESSAGE,
} from '../../../utils';
import { SelectOptimization } from '../../common/select-optimization.component';
import { TEST_NAME_ERRORS } from '../utils';
import { PreselectedModelInfo } from './preselected-model.component';
import { RunTestDialogContentProps } from './run-test-dialog.interface';
import { useRunTestDialogState } from './use-run-test-dialog-state.hook';

import classes from './run-test-dialog.module.scss';

export const RunTestDialogContent = ({
    modelsGroups,
    preselectedModel,
    handleClose,
}: RunTestDialogContentProps): JSX.Element => {
    const MAX_TEST_NAME_LENGTH = 30;

    const { workspaceId, projectId, organizationId } = useProjectIdentifier();

    const {
        models,
        selectedModelsGroup,
        selectedModelsGroupId,
        selectedModelId,
        handleChangeModelsGroup,
        handleChangeModel,
        taskWithNoModels,
        isLoadingModel,

        isOptimizationSelectionVisible,
        selectedOptimizationType,
        optimizationOptions,
        setSelectedOptimizationType,

        tasks,
        selectedTaskId,
        handleSelectTaskType,
        isTaskSelectionVisible,

        testName,
        errorInTestName,
        handleTestNameChange,

        datasets,
        selectedDatasetId,
        setSelectedDatasetId,
        isDefaultDatasetSelected,
        wasTestingSetTestedWithThisConfiguration,

        shouldShowMetricPicker,
        selectedMetric,
        handleSelectMetric,

        handleRunTest,
        isRunTestDisabled,
        isRunTestMutationLoading,
    } = useRunTestDialogState({
        modelsGroups,
        preselectedModel,
        handleClose,
    });

    // Select the first option by default
    useEffect(() => {
        if (optimizationOptions[0]) {
            setSelectedOptimizationType(optimizationOptions[0]);
        }

        // eslint-disable-next-line react-hooks/exhaustive-deps
    }, [optimizationOptions]);

    const validModelVersions = selectedModelsGroup?.modelVersions.filter((model) => !isModelDeleted(model));

    return (
        <>
            <Dialog>
                <Heading>Run test</Heading>
                <Divider />
                <Content UNSAFE_className={classes.hideArrowInDisabledPickers}>
                    <Flex direction={'column'} width={'100%'} height={'100%'} gap={'size-250'}>
                        {isTaskSelectionVisible && (
                            <Picker
                                label={'Task type'}
                                aria-label='Select task type'
                                placeholder={'Select task type'}
                                width={'100%'}
                                items={tasks}
                                selectedKey={selectedTaskId}
                                onSelectionChange={handleSelectTaskType}
                                id={'select-task-type-id'}
                            >
                                {(item) => (
                                    <Item aria-label={item.domain} key={item.id} textValue={item.domain}>
                                        {item.domain}
                                    </Item>
                                )}
                            </Picker>
                        )}
                        {taskWithNoModels ? (
                            <WarningMessage isVisible message={NO_MODELS_MESSAGE} marginTop={'size-250'} />
                        ) : (
                            <>
                                {preselectedModel ? (
                                    <PreselectedModelInfo
                                        taskName={tasks[0].domain}
                                        modelGroupName={`${models[0].modelTemplateName}
                                        (${models[0].groupName})`}
                                        modelVersion={`Version ${models[0].modelVersions[0].version}`}
                                        optimizationModelName={preselectedModel.optimizedModel?.text}
                                    />
                                ) : (
                                    <></>
                                )}
                                <TextField
                                    id={'input-test-name-id'}
                                    width={'100%'}
                                    value={testName}
                                    label={'Test name'}
                                    onChange={handleTestNameChange}
                                    validationState={errorInTestName ? 'invalid' : undefined}
                                    errorMessage={errorInTestName !== null ? TEST_NAME_ERRORS[errorInTestName] : ''}
                                    maxLength={MAX_TEST_NAME_LENGTH}
                                />
                                {!preselectedModel ? (
                                    <Flex alignItems={'center'} gap={'size-100'}>
                                        <Picker
                                            label={'Model'}
                                            items={models}
                                            width={'100%'}
                                            placeholder={'Select model'}
                                            selectedKey={selectedModelsGroupId}
                                            onSelectionChange={(key) => handleChangeModelsGroup(key, models)}
                                            isDisabled={!Boolean(selectedTaskId)}
                                            id={'select-model-group-id'}
                                        >
                                            {(item) => {
                                                const templateName = item.modelTemplateName ?? undefined;

                                                return (
                                                    <Item
                                                        aria-label={`
                                                            ${item.groupName} ${templateName && ` (${templateName})`}
                                                        `}
                                                        key={item.groupId}
                                                        textValue={item.groupName}
                                                    >{`
                                                        ${item.groupName} ${templateName && ` (${templateName})`}
                                                    `}</Item>
                                                );
                                            }}
                                        </Picker>

                                        {selectedModelsGroup && !isVisualPromptModel(selectedModelsGroup) && (
                                            <Picker
                                                label={'Version'}
                                                placeholder={'Select version'}
                                                items={validModelVersions ?? []}
                                                selectedKey={selectedModelId}
                                                onSelectionChange={handleChangeModel}
                                                isDisabled={!Boolean(selectedModelsGroup)}
                                                id={'select-model-version-id'}
                                            >
                                                {(item) => (
                                                    <Item
                                                        aria-label={`Version ${item.version}`}
                                                        key={item.id}
                                                        textValue={`Version ${item.version}`}
                                                    >
                                                        <Text>Version {item.version}</Text>
                                                    </Item>
                                                )}
                                            </Picker>
                                        )}
                                    </Flex>
                                ) : (
                                    <></>
                                )}
                                {isOptimizationSelectionVisible && (
                                    <SelectOptimization
                                        options={optimizationOptions}
                                        selectedOptimizationType={selectedOptimizationType}
                                        setSelectedOptimizationType={setSelectedOptimizationType}
                                        isLoading={isLoadingModel}
                                    />
                                )}
                                {shouldShowMetricPicker && (
                                    <Picker
                                        width={'100%'}
                                        label={'Evaluation metric'}
                                        placeholder={'Select evaluation metric'}
                                        items={METRIC_ITEMS}
                                        selectedKey={selectedMetric}
                                        onSelectionChange={handleSelectMetric}
                                        marginBottom={'size-250'}
                                        id={'select-metric-id'}
                                    >
                                        {(item) => (
                                            <Item
                                                aria-label={`metric ${item.name}`}
                                                key={item.name}
                                                textValue={item.name}
                                            >
                                                {item.name}
                                            </Item>
                                        )}
                                    </Picker>
                                )}
                                <View>
                                    <Picker
                                        width={'100%'}
                                        label={'Dataset'}
                                        placeholder={'Select dataset'}
                                        items={datasets}
                                        selectedKey={selectedDatasetId}
                                        onSelectionChange={(key) => setSelectedDatasetId(String(key))}
                                        marginBottom={isDefaultDatasetSelected ? 'size-100' : undefined}
                                        id={'select-dataset-id'}
                                    >
                                        {(item) => (
                                            <Item aria-label={item.name} key={item.id} textValue={item.name}>
                                                {item.name}
                                            </Item>
                                        )}
                                    </Picker>
                                    {isDefaultDatasetSelected && !!selectedDatasetId && (
                                        <WarningMessage
                                            isVisible={isDefaultDatasetSelected}
                                            message={
                                                <>
                                                    {DEFAULT_DATASET_MESSAGE}{' '}
                                                    <Link
                                                        to={paths.project.dataset.index({
                                                            organizationId,
                                                            workspaceId,
                                                            projectId,
                                                            datasetId: String(selectedDatasetId),
                                                        })}
                                                    >
                                                        Create testing set.
                                                    </Link>
                                                </>
                                            }
                                        />
                                    )}
                                </View>
                                <WarningMessage
                                    UNSAFE_className={classes.warningMessage}
                                    isVisible={wasTestingSetTestedWithThisConfiguration}
                                    message={TESTING_SET_WAS_TESTED_WITH_THIS_CONFIGURATION_MESSAGE}
                                />
                            </>
                        )}
                    </Flex>
                </Content>
                <ButtonGroup>
                    <Button variant={'secondary'} onPress={handleClose} id='dialog-cancel-button-id'>
                        Cancel
                    </Button>
                    <Button
                        isPending={isRunTestMutationLoading}
                        isDisabled={isRunTestDisabled}
                        onPress={handleRunTest}
                        id={'dialog-run-test-button-id'}
                    >
                        Run test
                    </Button>
                </ButtonGroup>
            </Dialog>
        </>
    );
};
