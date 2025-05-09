// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { CSSProperties } from 'react';

import {
    ButtonGroup,
    Content,
    Dialog,
    DialogContainer,
    Divider,
    Flex,
    Form,
    Heading,
    Text,
} from '@adobe/react-spectrum';
import { isFunction } from 'lodash-es';

import { useModels } from '../../../../../core/models/hooks/use-models.hook';
import { useProjectIdentifier } from '../../../../../hooks/use-project-identifier/use-project-identifier';
import { Button } from '../../../../../shared/components/button/button.component';
import { ButtonCreditsToConsume } from '../../project-model/components/button-credits-to-consume/button-credits-to-consume.component';
import { useCanTrainModel } from '../train-model-dialog/use-can-train-model.hook';
import { NotEnoughAnnotationsDialog } from './not-enough-annotations-dialog.component';
import { useTrainStateValue } from './use-training-state-value/use-training-state-value.hook';
import { TrainingSteps } from './use-training-state-value/use-training-state-value.interface';

import sharedClasses from '../../../../../shared/shared.module.scss';
import classes from './train-model-dialog.module.scss';

interface TrainModelDialogProps {
    isOpen: boolean;
    onClose: () => void;
    onSuccess?: () => void;
}

const dialogStyles = {
    '--spectrum-dialog-padding-x': 'var(--spectrum-global-dimension-size-250)',
    '--spectrum-dialog-padding-y': 'var(--spectrum-global-dimension-size-350)',
} as CSSProperties;

export const TrainModelDialog = ({ isOpen, onClose, onSuccess }: TrainModelDialogProps): JSX.Element => {
    const { useTrainModelMutation } = useModels();
    const trainModel = useTrainModelMutation();
    const projectIdentifier = useProjectIdentifier();

    const {
        stepConfig,
        showNextButton,
        showBackButton,
        nextAction,
        prevAction,
        selectedTask,
        trainingBodyDTO,
        handleDefaultStateOnClose,
        renderCurrentStep,
        handleChangeSelectedTask,
        tasks,
    } = useTrainStateValue();

    const isConfigParamsStep = stepConfig.key === TrainingSteps.CONFIGURABLE_PARAMETERS;

    const isAllowedToTrainModel = useCanTrainModel(projectIdentifier);
    const { canTrainModel, numberOfRequiredAnnotations } = isAllowedToTrainModel(selectedTask);

    const handleOnDismiss = (): void => {
        onClose();
        handleDefaultStateOnClose();
    };

    const handleSubmit = (): void => {
        trainModel.mutate(
            { projectIdentifier, body: trainingBodyDTO },
            {
                onSuccess: () => {
                    handleOnDismiss();
                    isFunction(onSuccess) && onSuccess();
                },
            }
        );
    };

    if (!canTrainModel) {
        return (
            <NotEnoughAnnotationsDialog
                isOpen={isOpen}
                onClose={handleOnDismiss}
                tasks={tasks}
                selectedTask={selectedTask}
                onTaskChange={handleChangeSelectedTask}
                numberOfRequiredAnnotations={numberOfRequiredAnnotations}
            />
        );
    }

    return (
        <DialogContainer onDismiss={handleOnDismiss}>
            {isOpen && (
                // we set height for the configurable parameters step because we don't want it to grow too much in
                // case we have lots of parameters
                <Dialog maxWidth={'100rem'} width={'80vw'} UNSAFE_style={dialogStyles}>
                    <Heading>
                        <Flex direction={'column'}>
                            Train model
                            <Flex
                                justifyContent={'space-between'}
                                alignItems={'center'}
                                UNSAFE_className={classes.trainingDialogDescription}
                            >
                                <Text marginTop={'size-50'}>{stepConfig.description}</Text>
                            </Flex>
                        </Flex>
                    </Heading>
                    <Divider marginBottom={'size-100'} />
                    <Content UNSAFE_className={trainModel.isPending ? sharedClasses.contentDisabled : ''}>
                        <Form height={isConfigParamsStep ? '100%' : 'auto'} UNSAFE_style={{ marginTop: 0 }}>
                            <>{renderCurrentStep(stepConfig.key)}</>
                        </Form>
                    </Content>
                    <ButtonGroup UNSAFE_className={classes.buttonGroup}>
                        <Button
                            variant={'secondary'}
                            onPress={handleOnDismiss}
                            id={'cancel-button-id'}
                            isDisabled={trainModel.isPending}
                        >
                            Cancel
                        </Button>
                        {showBackButton && (
                            <Button
                                variant={'primary'}
                                onPress={prevAction}
                                id={'back-button-id'}
                                isDisabled={trainModel.isPending}
                            >
                                Back
                            </Button>
                        )}
                        {showNextButton ? (
                            <Button variant={'primary'} onPress={nextAction} id={'next-button-id'}>
                                Next
                            </Button>
                        ) : (
                            <ButtonCreditsToConsume
                                aria-label={'Start'}
                                taskId={selectedTask.id}
                                getTooltip={(totalMedias) =>
                                    // eslint-disable-next-line max-len
                                    `Annotated dataset for this project contains ${totalMedias} images/frames that will be used for training`
                                }
                                isLoading={trainModel.isPending}
                                isDisabled={trainModel.isPending}
                                id={'start-button-id'}
                                onPress={handleSubmit}
                            />
                        )}
                    </ButtonGroup>
                </Dialog>
            )}
        </DialogContainer>
    );
};
