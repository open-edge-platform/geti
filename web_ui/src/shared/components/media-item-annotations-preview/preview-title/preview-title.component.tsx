// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { Heading } from '@geti/ui';

import classes from './preview-title.module.scss';

interface PreviewTitleProps {
    title: string;
    subTitle: string;
}

export const PreviewTitle = ({ title, subTitle }: PreviewTitleProps): JSX.Element => {
    return (
        <Heading id={'preview-title'} data-testid={'preview-title'}>
            <p className={classes.title}>{title}</p>
            <p className={classes.subTitle}>{subTitle}</p>
        </Heading>
    );
};
