// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

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
