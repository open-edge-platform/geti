// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { ComponentProps, ReactNode, useState } from 'react';

import { Flex, Header, View } from '@geti/ui';
import { ChevronDownLight, ChevronUpLight } from '@geti/ui/icons';

import { QuietActionButton } from '../quiet-button/quiet-action-button.component';

import classes from './accordion.module.scss';

interface AccordionProps extends ComponentProps<typeof View> {
    overflow?: 'auto' | 'hidden';
    header: ReactNode;
    idPrefix: string;
    children: ReactNode;
    dockIcon?: JSX.Element;
    isDisabled?: boolean;
    isFullHeight?: boolean;
    hasFoldButton?: boolean;
    defaultOpenState?: boolean;
    justifyContentHeader?: ComponentProps<typeof Flex>['justifyContent'];
}

export const Accordion = (props: AccordionProps): JSX.Element => {
    const {
        header,
        children,
        idPrefix,
        overflow = 'auto',
        isDisabled = false,
        isFullHeight = true,
        hasFoldButton = true,
        defaultOpenState = false,
        justifyContentHeader = 'space-between',
        ...rest
    } = props;
    const [isSelected, setIsSelected] = useState(defaultOpenState);

    return (
        <View
            {...rest}
            overflow={isFullHeight ? 'hidden' : ''}
            UNSAFE_className={[
                classes.accordion,
                isFullHeight ? classes.accordionHeight : '',
                rest.UNSAFE_className,
            ].join(' ')}
        >
            <Flex direction='column' height='100%'>
                <Header>
                    <Flex justifyContent={justifyContentHeader} alignItems='center'>
                        <>{header}</>
                        {hasFoldButton && (
                            <QuietActionButton
                                isDisabled={isDisabled}
                                onPress={() => setIsSelected(!isSelected)}
                                id={`${idPrefix}-fold-unfold-button`}
                                data-testid={`${idPrefix}-fold-unfold-button`}
                                aria-label={isSelected ? 'Close' : 'Open'}
                            >
                                {isSelected ? <ChevronUpLight /> : <ChevronDownLight />}
                            </QuietActionButton>
                        )}
                    </Flex>
                </Header>

                {isSelected ? (
                    <Flex direction={'column'} flex={1} UNSAFE_style={{ overflow }}>
                        {children}
                    </Flex>
                ) : (
                    <></>
                )}
            </Flex>
        </View>
    );
};
