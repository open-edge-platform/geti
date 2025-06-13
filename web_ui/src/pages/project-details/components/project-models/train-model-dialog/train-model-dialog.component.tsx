// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { FC } from 'react';

import { Button, ButtonGroup, Content, Dialog, DialogContainer, Divider, Heading } from '@geti/ui';
import { isFunction } from 'lodash-es';

import { useModels } from '../../../../../core/models/hooks/use-models.hook';
import { useProjectIdentifier } from '../../../../../hooks/use-project-identifier/use-project-identifier';
import { ButtonCreditsToConsume } from '../../project-model/components/button-credits-to-consume/button-credits-to-consume.component';
import { AdvancedSettings } from './advanced-settings/advanced-settings.component';
import { NotEnoughAnnotationsDialog } from './not-enough-annotations-dialog.component';
import { TrainModelBasic } from './train-model-basic.component';
import { useCanTrainModel } from './use-can-train-model.hook';
import { useTrainModelState } from './use-train-model-state.hook';

interface TrainModelProps {
    isOpen: boolean;
    onClose: () => void;
    onSuccess?: () => void;
}

interface TrainModelDialogProps {
    onClose: () => void;
    onSuccess?: () => void;
    isAllowedToTrainModel: ReturnType<typeof useCanTrainModel>;
}

const TrainModelDialog: FC<TrainModelDialogProps> = ({ onClose, onSuccess, isAllowedToTrainModel }) => {
    const projectIdentifier = useProjectIdentifier();

    const { useTrainModelMutation } = useModels();
    const trainModel = useTrainModelMutation();

    const {
        isBasicMode,
        openAdvancedSettingsMode,
        algorithms,
        selectedModelTemplateId,
        changeSelectedTemplateId,
        activeModelTemplateId,
        selectedTask,
        changeTask,
        tasks,
        trainingBodyDTO,
        isTaskChainProject,
        isReshufflingSubsetsEnabled,
        changeReshufflingSubsetsEnabled,
        configParameters,
        changeTrainFromScratch,
        trainFromScratch,
    } = useTrainModelState();

    const { canTrainModel, numberOfRequiredAnnotations } = isAllowedToTrainModel(selectedTask);

    const handleSubmit = (): void => {
        trainModel.mutate(
            { projectIdentifier, body: trainingBodyDTO },
            {
                onSuccess: () => {
                    onClose();
                    isFunction(onSuccess) && onSuccess();
                },
            }
        );
    };

    if (!canTrainModel) {
        return (
            <NotEnoughAnnotationsDialog
                onClose={onClose}
                tasks={tasks}
                selectedTask={selectedTask}
                onTaskChange={changeTask}
                numberOfRequiredAnnotations={numberOfRequiredAnnotations}
            />
        );
    }

    return (
        <Dialog maxWidth={'100rem'} width={'80vw'} height={isBasicMode ? undefined : '80vh'}>
            <Heading>Train Model</Heading>
            <Divider />
            <Content>
                {isBasicMode || configParameters === undefined ? (
                    <TrainModelBasic
                        selectedTask={selectedTask}
                        tasks={tasks}
                        onTaskChange={changeTask}
                        isTaskChainProject={isTaskChainProject}
                        activeModelTemplateId={activeModelTemplateId}
                        selectedModelTemplateId={selectedModelTemplateId}
                        onChangeSelectedTemplateId={changeSelectedTemplateId}
                        algorithms={algorithms}
                    />
                ) : (
                    <AdvancedSettings
                        configParameters={configParameters}
                        selectedModelTemplateId={selectedModelTemplateId}
                        onChangeSelectedTemplateId={changeSelectedTemplateId}
                        algorithms={algorithms}
                        activeModelTemplateId={activeModelTemplateId}
                        isReshufflingSubsetsEnabled={isReshufflingSubsetsEnabled}
                        onReshufflingSubsetsEnabledChange={changeReshufflingSubsetsEnabled}
                        trainFromScratch={trainFromScratch}
                        onTrainFromScratchChange={changeTrainFromScratch}
                    />
                )}
            </Content>

            <ButtonGroup UNSAFE_style={{ flexWrap: 'wrap' }}>
                <Button variant={'secondary'} onPress={onClose}>
                    Cancel
                </Button>
                {isBasicMode && (
                    <Button variant={'secondary'} onPress={openAdvancedSettingsMode}>
                        Advanced settings
                    </Button>
                )}
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
            </ButtonGroup>
        </Dialog>
    );
};

export const TrainModel: FC<TrainModelProps> = ({ isOpen, onClose, onSuccess }) => {
    const projectIdentifier = useProjectIdentifier();
    const canTrainModel = useCanTrainModel(projectIdentifier);

    return (
        <DialogContainer onDismiss={onClose}>
            {isOpen && (
                <TrainModelDialog onClose={onClose} onSuccess={onSuccess} isAllowedToTrainModel={canTrainModel} />
            )}
        </DialogContainer>
    );
};
