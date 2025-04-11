// INTEL CONFIDENTIAL
//
// Copyright (C) 2021 Intel Corporation
//
// This software and the related documents are Intel copyrighted materials, and your use of them is governed by
// the express license under which they were provided to you ("License"). Unless the License provides otherwise,
// you may not use, modify, copy, publish, distribute, disclose or transmit this software or the related documents
// without Intel's prior written permission.
//
// This software and the related documents are provided as is, with no express or implied warranties,
// other than those that are expressly stated in the License.

import { ButtonGroup, Content, Dialog, DialogContainer, Divider, Heading } from '@adobe/react-spectrum';

import { Button } from '../../../../shared/components/button/button.component';

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
