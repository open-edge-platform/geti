// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

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
