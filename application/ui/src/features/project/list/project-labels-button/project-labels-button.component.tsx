// Copyright (C) 2026 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

import type { Label } from '@/api/types';
import { useTranslation } from '@/i18n';
import { ActionButton, Content, Dialog, DialogTrigger, Flex, Heading, Text } from '@geti-ui/ui';
import { Tag } from '@geti-ui/ui/icons';

import classes from './project-labels-button.module.scss';

type ProjectLabelsButtonProps = {
    labels: Label[];
};

export const ProjectLabelsButton = ({ labels }: ProjectLabelsButtonProps) => {
    const { t } = useTranslation();

    if (labels.length === 0) {
        return null;
    }

    return (
        <DialogTrigger hideArrow type='popover'>
            <ActionButton isQuiet aria-label={'View project labels'}>
                <Tag />
            </ActionButton>

            <Dialog width={'size-2400'} aria-label={t('project.list.card.labelsDialog.title')}>
                <Content>
                    <Flex direction={'column'} gap={'size-100'}>
                        <Heading level={4} margin={0}>
                            {t('project.list.card.labelsDialog.title')}
                        </Heading>

                        <Flex wrap gap={'size-100'}>
                            {labels.map((label) => (
                                <Flex key={label.id} alignItems={'center'} gap={'size-75'}>
                                    <span
                                        aria-hidden
                                        style={{ backgroundColor: label.color }}
                                        className={classes.labelDot}
                                    />
                                    <Text>{label.name}</Text>
                                </Flex>
                            ))}
                        </Flex>
                    </Flex>
                </Content>
            </Dialog>
        </DialogTrigger>
    );
};
