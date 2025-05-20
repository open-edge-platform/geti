// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { Button, ButtonGroup, Content, Dialog, DialogContainer, Divider, Heading, Text } from '@geti/ui';
import { OverlayTriggerState } from 'react-stately';

import { useModels } from '../../../../../../core/models/hooks/use-models.hook';
import { useProjectIdentifier } from '../../../../../../hooks/use-project-identifier/use-project-identifier';

interface DeleteModelDialogProps {
    version: number;
    groupId: string;
    modelId: string;
    modelName: string;
    overlayState: OverlayTriggerState;
}

export const DeleteModelDialog = ({
    overlayState,
    version,
    groupId,
    modelId,
    modelName,
}: DeleteModelDialogProps): JSX.Element => {
    const { useArchiveModelMutation } = useModels();
    const archiveModelMutation = useArchiveModelMutation();
    const projectIdentifier = useProjectIdentifier();

    return (
        <DialogContainer type={'modal'} onDismiss={overlayState.toggle}>
            {overlayState.isOpen && (
                <Dialog maxWidth={'74rem'}>
                    <Heading>
                        {modelName} model version {version}
                    </Heading>

                    <Divider />

                    <Content>
                        <Text>
                            This action will delete the model binary files in storage for &quot;{modelName}&quot; model
                            version &quot;{version}&quot;. The model metadata (e.g., dataset and model statistics) will
                            still be available. Do you want to proceed?
                        </Text>

                        <Divider size={'M'} marginTop={'size-150'} />
                    </Content>

                    <ButtonGroup>
                        <Button
                            variant={'primary'}
                            onPress={overlayState.close}
                            aria-label={'close delete dialog'}
                            id={'close-delete-button'}
                        >
                            Close
                        </Button>
                        <Button
                            variant={'accent'}
                            aria-label={'delete model'}
                            id={'delete-button'}
                            onPress={() =>
                                archiveModelMutation.mutate(
                                    { ...projectIdentifier, groupId, modelId },
                                    { onSuccess: overlayState.close }
                                )
                            }
                            isPending={archiveModelMutation.isPending}
                        >
                            Delete
                        </Button>
                    </ButtonGroup>
                </Dialog>
            )}
        </DialogContainer>
    );
};
