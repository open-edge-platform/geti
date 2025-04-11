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

import { DOMAIN } from '../../../../core/projects/core.interface';
import { DomainStepProps } from './domain-step.interface';
import { SelectDomainButton } from './select-domain-button.component';

export const useDomainButtons = ({ domains, handleSelection, isValid, selected }: DomainStepProps) => {
    const getDomainButton = (domain: DOMAIN, isNextEnabled = true): JSX.Element => {
        switch (domain) {
            case DOMAIN.DETECTION:
                const isSelected = selected === DOMAIN.DETECTION;
                return (
                    <SelectDomainButton
                        taskNumber={1}
                        id={'detection-step'}
                        text={'Detection'}
                        isDone={!isSelected}
                        select={() => handleSelection(DOMAIN.DETECTION)}
                        isSelected={isSelected}
                    />
                );
            case DOMAIN.SEGMENTATION:
                return (
                    <SelectDomainButton
                        taskNumber={2}
                        id={'segmentation-step'}
                        text={'Segmentation'}
                        select={() => handleSelection(DOMAIN.SEGMENTATION)}
                        isSelected={selected === DOMAIN.SEGMENTATION}
                        isDisabled={selected !== DOMAIN.SEGMENTATION ? !isNextEnabled : false}
                    />
                );
            case DOMAIN.CLASSIFICATION:
                return (
                    <SelectDomainButton
                        taskNumber={2}
                        id={'classification-step'}
                        text={'Classification'}
                        select={() => handleSelection(DOMAIN.CLASSIFICATION)}
                        isSelected={selected === DOMAIN.CLASSIFICATION}
                        isDisabled={selected !== DOMAIN.CLASSIFICATION ? !isNextEnabled : false}
                    />
                );
            default:
                throw new Error('Unsupported domain in chain');
        }
    };

    return {
        firstDomainButton: getDomainButton(domains[0]),
        secondDomainButton: getDomainButton(domains[1], isValid),
    };
};
