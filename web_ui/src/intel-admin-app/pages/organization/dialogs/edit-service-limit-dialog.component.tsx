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

import { useEffect, useState } from 'react';

import {
    ButtonGroup,
    Content,
    Dialog,
    DialogContainer,
    Divider,
    Form,
    Heading,
    NumberField,
} from '@adobe/react-spectrum';
import capitalize from 'lodash/capitalize';

import { Quota } from '../../../../core/credits/subscriptions/quotas.interface';
import { Button } from '../../../../shared/components/button/button.component';

interface EditServiceLimitDialogProps {
    quota: Quota;
    onSave: (quota: Quota) => void;
    isOpen: boolean;
    onOpenChange: (isOpen: boolean) => void;
    isLoading?: boolean;
}

const MIN_SERVICE_LIMIT = 1;

export const EditServiceLimitDialog = ({
    quota,
    onSave,
    isOpen,
    onOpenChange,
    isLoading,
}: EditServiceLimitDialogProps) => {
    const [limit, setLimit] = useState(quota.limit);
    const isSaveButtonDisabled = limit === quota.limit;

    useEffect(() => {
        if (isOpen) {
            setLimit(quota.limit);
        }
    }, [isOpen, quota.limit]);

    const onSubmit = () => {
        onSave({ ...quota, limit });
    };

    return (
        <DialogContainer onDismiss={() => isLoading !== true && onOpenChange(false)}>
            {isOpen && (
                <Dialog>
                    <Heading>Edit service limit</Heading>
                    <Divider size='S' />
                    <Content>
                        <Form
                            onSubmit={(event) => {
                                event.preventDefault();
                                onSubmit();
                            }}
                        >
                            <NumberField
                                label={`${capitalize(quota.serviceName)} - ${quota.quotaName}`}
                                value={limit}
                                id='service-limit-value-input'
                                minValue={MIN_SERVICE_LIMIT}
                                maxValue={quota.maxLimit ?? Number.MAX_SAFE_INTEGER}
                                // eslint-disable-next-line jsx-a11y/no-autofocus
                                autoFocus
                                onFocus={(event) => {
                                    (event.target as HTMLInputElement).select();
                                }}
                                onChange={(value) => setLimit(value)}
                            />
                        </Form>
                    </Content>
                    <ButtonGroup>
                        <Button variant='secondary' onPress={() => onOpenChange(false)} isDisabled={isLoading}>
                            Cancel
                        </Button>
                        <Button
                            variant='accent'
                            isPending={isLoading}
                            isDisabled={isSaveButtonDisabled}
                            onPress={onSubmit}
                        >
                            Save
                        </Button>
                    </ButtonGroup>
                </Dialog>
            )}
        </DialogContainer>
    );
};
