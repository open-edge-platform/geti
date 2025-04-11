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

import { render } from '@testing-library/react';

import { DOMAIN } from '../../../../core/projects/core.interface';
import { getById } from '../../../../test-utils/utils';
import { DomainChainSteps } from './domain-chain-steps.component';

describe('Domain chain steps', () => {
    it('Show proper domains', () => {
        const { container } = render(
            <DomainChainSteps
                domains={[DOMAIN.DETECTION, DOMAIN.CLASSIFICATION]}
                handleSelection={() => {
                    /**/
                }}
                isValid={true}
                selected={DOMAIN.CLASSIFICATION}
            />
        );

        const detection = getById(container, 'detection-step');
        const classification = getById(container, 'classification-step');
        expect(detection).toBeInTheDocument();
        expect(classification).toBeInTheDocument();
    });

    it('Selection is properly marked', () => {
        const { container } = render(
            <DomainChainSteps
                domains={[DOMAIN.DETECTION, DOMAIN.CLASSIFICATION]}
                handleSelection={() => {
                    /**/
                }}
                isValid={true}
                selected={DOMAIN.CLASSIFICATION}
            />
        );

        const detection = getById(container, 'detection-step');
        const classification = getById(container, 'classification-step');
        expect(classification).toHaveClass('selected', { exact: false });
        expect(detection).not.toHaveClass('selected', { exact: false });
    });

    it('When first domain is not valid the last one is disabled', () => {
        const { container } = render(
            <DomainChainSteps
                domains={[DOMAIN.DETECTION, DOMAIN.CLASSIFICATION]}
                handleSelection={() => {
                    /**/
                }}
                isValid={false}
                selected={DOMAIN.DETECTION}
            />
        );

        const detection = getById(container, 'detection-step');
        const classification = getById(container, 'classification-step');
        expect(classification).toHaveAttribute('disabled');
        expect(detection).not.toHaveAttribute('disabled');
    });
});
