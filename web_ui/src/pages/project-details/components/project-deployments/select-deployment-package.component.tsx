// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { FC } from 'react';

import { Flex, Item, Picker, Link as SpectrumLink, Text } from '@geti/ui';
import { Link } from 'react-router-dom';

import { useDocsUrl } from '../../../../hooks/use-docs-url/use-docs-url.hook';
import { InfoTooltip } from '../../../../shared/components/info-tooltip/info-tooltip.component';
import { DocsUrl } from '../../../../shared/components/tutorials/utils';

export enum DEPLOYMENT_PACKAGE_TYPES {
    CODE_DEPLOYMENT = 'Code deployment',
    OVMS_DEPLOYMENT = 'OpenVINO Model Server deployment',
}

interface SelectDeploymentPackageProps {
    selectedDeploymentPackageType: DEPLOYMENT_PACKAGE_TYPES;
    onSelectDeploymentPackageType: (deploymentPackageType: DEPLOYMENT_PACKAGE_TYPES) => void;
    isDisabled?: boolean;
}

const TooltipText = () => {
    const docsUrl = useDocsUrl();
    const codeDeploymentDocsUrl = `${docsUrl}${DocsUrl.CODE_DEPLOYMENT}`;

    return (
        <Flex direction={'column'} gap={'size-100'}>
            <Text>
                <strong>Code deployment:</strong> to run the model locally using Geti SDK.
            </Text>
            <Text>
                <strong>OpenVINO Model Server deployment:</strong> to deploy the model locally on OpenVINO Model Server.
            </Text>
            <Text>
                For more information please visit{' '}
                <SpectrumLink>
                    <Link to={codeDeploymentDocsUrl} target={'_blank'} rel={'noopener noreferrer'}>
                        our official documentation
                    </Link>
                </SpectrumLink>
                .
            </Text>
        </Flex>
    );
};

const PickerLabel = () => {
    return (
        <Flex alignItems={'center'} gap={'size-50'}>
            Deployment package <InfoTooltip tooltipText={<TooltipText />} id={'single-task-deployment-info'} />
        </Flex>
    );
};

export const SelectDeploymentPackage: FC<SelectDeploymentPackageProps> = ({
    selectedDeploymentPackageType,
    onSelectDeploymentPackageType,
    isDisabled = false,
}) => {
    return (
        <Picker
            width={'100%'}
            label={<PickerLabel />}
            selectedKey={selectedDeploymentPackageType}
            onSelectionChange={(key) => onSelectDeploymentPackageType(key as DEPLOYMENT_PACKAGE_TYPES)}
            isDisabled={isDisabled}
        >
            <Item key={DEPLOYMENT_PACKAGE_TYPES.CODE_DEPLOYMENT}>{DEPLOYMENT_PACKAGE_TYPES.CODE_DEPLOYMENT}</Item>
            <Item key={DEPLOYMENT_PACKAGE_TYPES.OVMS_DEPLOYMENT}>{DEPLOYMENT_PACKAGE_TYPES.OVMS_DEPLOYMENT}</Item>
        </Picker>
    );
};
