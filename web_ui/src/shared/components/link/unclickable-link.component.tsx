// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { Link, LinkProps } from 'react-router-dom';

import classes from './unclickable-link.module.scss';

export const UnClickableLink = (props: LinkProps & Omit<React.RefAttributes<HTMLAnchorElement>, 'onClick'>) => (
    <Link {...props} onClick={(e) => e.preventDefault()} className={classes.unClickableLink} />
);
