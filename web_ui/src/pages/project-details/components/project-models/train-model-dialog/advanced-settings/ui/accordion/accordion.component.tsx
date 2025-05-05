// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { ComponentProps, FC, ReactNode } from 'react';

import { Disclosure, DisclosurePanel, DisclosureTitle, Divider, Flex, Text, View } from '@adobe/react-spectrum';
import clsx from 'clsx';

import { AlertOutlined } from '../../../../../../../../assets/icons';

import styles from './accordion.module.scss';

type DisclosureProps = Omit<ComponentProps<typeof Disclosure>, 'isQuiet'>;
type DisclosureTitleProps = ComponentProps<typeof DisclosureTitle>;
type DisclosurePanelProps = ComponentProps<typeof DisclosurePanel>;

interface AccordionTag {
    children: ReactNode;
}

const AccordionTitle: FC<DisclosureTitleProps> = ({ UNSAFE_className, ...props }) => {
    return <DisclosureTitle {...props} UNSAFE_className={clsx(UNSAFE_className, styles.accordionTitle)} />;
};

export const RawContent: FC<{ children: ReactNode }> = ({ children }) => {
    return <View UNSAFE_className={styles.accordionContent}>{children}</View>;
};

const AccordionContent: FC<DisclosurePanelProps> = ({ UNSAFE_className, ...props }) => {
    return <DisclosurePanel {...props} UNSAFE_className={clsx(UNSAFE_className, styles.accordionContent)} />;
};

const AccordionTag: FC<AccordionTag> = ({ children }) => {
    return (
        <View borderRadius={'regular'} borderWidth={'thin'} padding={'size-50'} UNSAFE_className={styles.accordionTag}>
            {children}
        </View>
    );
};

const AccordionDivider: FC<Omit<ComponentProps<typeof Divider>, 'size'>> = (props) => {
    return <Divider size={'S'} {...props} />;
};

const AccordionDescription: FC<{ children: ReactNode }> = ({ children }) => {
    return <Text UNSAFE_className={styles.accordionDescription}>{children}</Text>;
};

const AccordionWarning: FC<{ children: ReactNode }> = ({ children }) => {
    return (
        <Flex alignItems={'center'} gap={'size-100'} UNSAFE_className={styles.warning}>
            <AlertOutlined />
            {children}
        </Flex>
    );
};

export const Accordion = ({ UNSAFE_className, ...props }: DisclosureProps) => {
    return <Disclosure isQuiet {...props} UNSAFE_className={clsx(UNSAFE_className, styles.accordion)} />;
};

Accordion.Title = AccordionTitle;
Accordion.Content = AccordionContent;
Accordion.Tag = AccordionTag;
Accordion.Divider = AccordionDivider;
Accordion.Description = AccordionDescription;
Accordion.Warning = AccordionWarning;
