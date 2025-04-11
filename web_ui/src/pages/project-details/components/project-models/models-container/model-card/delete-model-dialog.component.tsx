// INTEL CONFIDENTIAL
//
// Copyright (C) 2024 Intel Corporation
//
// This software and the related documents are Intel copyrighted materials, and your use of them is governed by
// the express license under which they were provided to you ("License"). Unless the License provides otherwise,
// you may not use, modify, copy, publish, distribute, disclose or transmit this software or the related documents
// without Intel's prior written permission.
//
// This software and the related documents are provided as is, with no express or implied warranties,
// other than those that are expressly stated in the License.

import { ButtonGroup, Content, Dialog, DialogContainer, Divider, Heading, Text } from '@adobe/react-spectrum';
import { OverlayTriggerState } from 'react-stately';

import { useModels } from '../../../../../../core/models/hooks/use-models.hook';
import { useProjectIdentifier } from '../../../../../../hooks/use-project-identifier/use-project-identifier';
import { Button } from '../../../../../../shared/components/button/button.component';

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
