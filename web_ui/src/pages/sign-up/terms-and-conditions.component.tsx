// INTEL CONFIDENTIAL
//
// Copyright (C) 2025 Intel Corporation
//
// This software and the related documents are Intel copyrighted materials, and your use of them is governed by
// the express license under which they were provided to you ("License"). Unless the License provides otherwise,
// you may not use, modify, copy, publish, distribute, disclose or transmit this software or the related documents
// without Intel's prior written permission.
//
// This software and the related documents are provided as is, with no express or implied warranties,
// other than those that are expressly stated in the License.

import { FC } from 'react';

import { Flex } from '@adobe/react-spectrum';

import { TERMS_OF_USE_GETI } from '../../core/const';
import { Checkbox } from '../../shared/components/checkbox/checkbox.component';

import classes from './terms-and-conditions.module.scss';

interface TermsAndConditionsProps {
    isChecked: boolean;
    onCheckedChange: (checked: boolean) => void;
}

const TermsAndConditionsLink = ({ children }: { children: string }) => {
    return (
        <a
            className={classes.termsAndConditionsLink}
            href={TERMS_OF_USE_GETI}
            target={'_blank'}
            rel={'noopener noreferrer'}
            id={'read-terms-link'}
        >
            {children}
        </a>
    );
};

export const TermsAndConditions: FC<TermsAndConditionsProps> = ({ isChecked, onCheckedChange }) => {
    return (
        <Flex UNSAFE_className={classes.termsAndConditionsCheckboxContainer}>
            <Checkbox isSelected={isChecked} onChange={onCheckedChange} id={'accept-terms-checkbox-input'} />
            <label htmlFor={'accept-terms-checkbox-input'}>
                I acknowledge that I have read and understood the{' '}
                <TermsAndConditionsLink>Terms and Conditions</TermsAndConditionsLink> for use of Intel® Geti™ and I
                agree my use of Intel® Geti™ will at all times comply with the{' '}
                <TermsAndConditionsLink>Terms and Conditions</TermsAndConditionsLink> for Intel® Geti™.
            </label>
        </Flex>
    );
};
