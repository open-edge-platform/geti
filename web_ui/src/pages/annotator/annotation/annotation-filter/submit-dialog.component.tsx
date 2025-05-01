// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { ButtonGroup, Content, Dialog, DialogContainer, Divider, Heading } from '@adobe/react-spectrum';
import { Button } from '@shared/components/button/button.component';

interface ConfirmationDialogProps {
    onCancel: () => Promise<void>;
    onSubmit: () => Promise<void>;
    onClearFilter: () => Promise<void>;
}

export const SubmitDialog = ({ onCancel, onSubmit, onClearFilter }: ConfirmationDialogProps): JSX.Element => {
    return (
        <DialogContainer onDismiss={onCancel} isDismissable={false}>
            <Dialog size='M'>
                <Heading>Filter applied</Heading>
                <Divider />
                <Content>
                    Some annotations are not shown. Submit the image now or clear the filter and show all annotations
                    before you submit it?
                </Content>

                <ButtonGroup>
                    <Button variant='secondary' onPress={onCancel} id='cancel-saving-confirmation'>
                        Cancel
                    </Button>
                    <Button variant='negative' onPress={onClearFilter} id='discard-saving-confirmation'>
                        Clear filter
                    </Button>
                    <Button variant='accent' onPress={onSubmit} id='submit-saving-confirmation'>
                        Submit anyway
                    </Button>
                </ButtonGroup>
            </Dialog>
        </DialogContainer>
    );
};
