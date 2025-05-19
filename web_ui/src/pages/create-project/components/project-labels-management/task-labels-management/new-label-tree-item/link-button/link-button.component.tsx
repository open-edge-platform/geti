// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { Flex, FlexStyleProps, Link } from '@geti/ui';

import { InfoTooltip } from '../../../../../../../shared/components/info-tooltip/info-tooltip.component';
import { idMatchingFormat } from '../../../../../../../test-utils/id-utils';

interface LinkButtonProps extends FlexStyleProps {
    text: string;
    isOpen: boolean;
    onOpen: () => void;
    info?: string;
    children: JSX.Element;
}

export const LinkButton = ({ text, info, children, isOpen, onOpen, ...props }: LinkButtonProps): JSX.Element => {
    return (
        <Flex alignItems={'center'} {...props}>
            {isOpen ? (
                children
            ) : (
                <Link
                    variant={'primary'}
                    onPress={() => {
                        onOpen();
                    }}
                    UNSAFE_style={{
                        fontSize: '12px',
                        textDecoration: 'none',
                        minWidth: 'max-content',
                        color: 'var(--spectrum-global-color-gray-900)',
                    }}
                >
                    {text}
                </Link>
            )}

            {info && <InfoTooltip tooltipText={info} id={idMatchingFormat(text)} />}
        </Flex>
    );
};
