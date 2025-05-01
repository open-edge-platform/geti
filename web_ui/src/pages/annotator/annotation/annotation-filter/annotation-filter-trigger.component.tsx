// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { useState } from 'react';

import { DialogTrigger, Tooltip, TooltipTrigger } from '@adobe/react-spectrum';
import { CornerIndicator } from '@shared/components/corner-indicator/corner-indicator.component';
import { QuietToggleButton } from '@shared/components/quiet-button/quiet-toggle-button.component';
import isEmpty from 'lodash/isEmpty';

import { Filter } from '../../../../assets/icons';
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
