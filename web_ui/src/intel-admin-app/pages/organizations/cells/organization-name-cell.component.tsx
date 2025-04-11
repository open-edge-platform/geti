// INTEL CONFIDENTIAL
//
// Copyright (C) 2023 Intel Corporation
//
// This software and the related documents are Intel copyrighted materials, and your use of them is governed by
// the express license under which they were provided to you ("License"). Unless the License provides otherwise,
// you may not use, modify, copy, publish, distribute, disclose or transmit this software or the related documents
// without Intel's prior written permission.
//
// This software and the related documents are provided as is, with no express or implied warranties,
// other than those that are expressly stated in the License.

import { Flex, Tooltip, TooltipTrigger } from '@adobe/react-spectrum';

import { ActionElement } from '../../../../shared/components/action-element/action-element.component';
import { PhotoPlaceholder } from '../../../../shared/components/photo-placeholder/photo-placeholder.component';
import { TruncatedText } from '../../../../shared/components/truncated-text/truncated-text.component';
import { OrganizationAdminsCopyText } from './organization-admins-copy-text.component';

interface OrganizationNameCellProps {
    id: string;
    name: string;
}

export const OrganizationNameCell = ({ id, name }: OrganizationNameCellProps): JSX.Element => {
    return (
        <Flex width={'100%'} alignItems={'center'} gap={'size-100'}>
            <PhotoPlaceholder name={name} email={name} width={'size-300'} height={'size-300'} />
            <TooltipTrigger placement={'bottom left'}>
                <ActionElement>
                    <TruncatedText>{name}</TruncatedText>
                </ActionElement>
                <Tooltip>
                    <OrganizationAdminsCopyText
                        text={id}
                        aria-label={'Copy id'}
                        data-testid={`copy-id-${id}`}
                        confirmationMessage={'Id copied successfully'}
                    />
                </Tooltip>
            </TooltipTrigger>
        </Flex>
    );
};
