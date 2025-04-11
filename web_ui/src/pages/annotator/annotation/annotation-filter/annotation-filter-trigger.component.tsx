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

import { useState } from 'react';

import { DialogTrigger, Tooltip, TooltipTrigger } from '@adobe/react-spectrum';
import isEmpty from 'lodash/isEmpty';

import { Filter } from '../../../../assets/icons';
import { CornerIndicator } from '../../../../shared/components/corner-indicator/corner-indicator.component';
import { QuietToggleButton } from '../../../../shared/components/quiet-button/quiet-toggle-button.component';
import { AnnotationFilterDialog } from './annotation-filter-dialog.component';
import { useAnnotationFilters } from './use-annotation-filters.hook';

interface AnnotationsFilterTriggerProps {
    isDisabled: boolean;
}

export const AnnotationsFilterTrigger = ({ isDisabled }: AnnotationsFilterTriggerProps): JSX.Element => {
    const [filters] = useAnnotationFilters();
    const isAnnotationsFilterEmpty = isEmpty(filters);

    const [isOpen, setIsOpen] = useState(false);

    return (
        <DialogTrigger hideArrow type={'popover'} onOpenChange={setIsOpen}>
            <TooltipTrigger placement={'bottom'}>
                <CornerIndicator isActive={!isAnnotationsFilterEmpty}>
                    <QuietToggleButton
                        id={'label-filter-modal-trigger'}
                        isSelected={isOpen}
                        isDisabled={isDisabled}
                        aria-label={'Filter annotations'}
                    >
                        <Filter />
                    </QuietToggleButton>
                </CornerIndicator>
                <Tooltip>Filter annotations</Tooltip>
            </TooltipTrigger>
            <AnnotationFilterDialog />
        </DialogTrigger>
    );
};
