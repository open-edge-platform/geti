// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { FC } from 'react';

import { Tag } from '@geti/ui';

import classes from '../models-container/model-card/model-card.module.scss';

interface TemplateNameTagProps {
    name: string;
}

export const TemplateNameTag: FC<TemplateNameTagProps> = ({ name }) => {
    return <Tag text={name} withDot={false} className={classes.templateNameTag} />;
};
